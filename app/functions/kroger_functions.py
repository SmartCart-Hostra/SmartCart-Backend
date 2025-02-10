import os
import requests
from flask import jsonify,request
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Kroger API credentials
CLIENT_ID = os.getenv('KROGER_CLIENT_ID')
CLIENT_SECRET = os.getenv('KROGER_CLIENT_SECRET')
LOCATION_ID = '01400943'  # Default location ID

def get_access_token():
    """
    Get an access token from the Kroger API using client credentials.
    """
    url = "https://api.kroger.com/v1/connect/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "scope": "product.compact"
    }
    try:
        response = requests.post(
            url,
            headers=headers,
            data=data,
            auth=(CLIENT_ID, CLIENT_SECRET)
        )
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"Error getting Kroger access token: {e}")
        return None

def search_products(query, access_token):
    """
    Search for products using the Kroger API.
    """
    url = f"https://api.kroger.com/v1/products?filter.term={query}&filter.locationId={LOCATION_ID}"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error searching Kroger products: {e}")
        return None

def get_kroger_product_details(ingredient_name, access_token):
    """
    Get detailed product information for a specific ingredient from the Kroger API.
    """
    # First, search for the product
    search_url = f"https://api.kroger.com/v1/products?filter.term={ingredient_name}&filter.locationId={LOCATION_ID}"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    try:
        # Search for product
        search_response = requests.get(search_url, headers=headers)
        search_data = search_response.json()

        if not search_data.get('data'):
            return None

        # Get first product from search results
        product_id = search_data['data'][0]['productId']

        # Get detailed product information
        product_url = f"https://api.kroger.com/v1/products/{product_id}?filter.locationId={LOCATION_ID}"
        product_response = requests.get(product_url, headers=headers)
        product_data = product_response.json()

        if not product_data.get('data'):
            return None

        product = product_data['data']
        return {
            'name': ingredient_name,
            'productId': product['productId'],
            'upc': product['upc'],
            'description': product['description'],
            'brand': product['brand'],
            'categories': product['categories'],
            'countryOrigin': product.get('countryOrigin'),
            'temperature': product.get('temperature'),
            'images': product.get('images', []),
            'items': [{
                'itemId': item['itemId'],
                'price': item['price'],
                'size': item['size'],
                'soldBy': item['soldBy'],
                'inventory': item.get('inventory'),
                'fulfillment': item.get('fulfillment')
            } for item in product.get('items', [])]
        }
    except Exception as e:
        print(f"Error fetching product details for {ingredient_name}: {str(e)}")
        return None

def kroger_search():
    """
    Search for Kroger products based on a query.
    """
    query = request.args.get("query")
    if not query:
        return jsonify({'error': 'No search query provided'}), 400

    try:
        access_token = get_access_token()
        if not access_token:
            return jsonify({'error': 'Failed to get Kroger access token'}), 500

        search_url = f"https://api.kroger.com/v1/products?filter.term={query}&filter.locationId={LOCATION_ID}"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        search_response = requests.get(search_url, headers=headers)
        search_data = search_response.json()

        if not search_data.get('data'):
            return jsonify({
                'query': query,
                'products': []
            })

        products = []
        for search_product in search_data['data']:
            try:
                product_id = search_product['productId']
                product_url = f"https://api.kroger.com/v1/products/{product_id}?filter.locationId={LOCATION_ID}"

                product_response = requests.get(product_url, headers=headers)
                product_data = product_response.json()

                product = product_data.get('data', {})

                # Create a product dictionary with default values for missing data
                product_info = {
                    'productId': product.get('productId', 'N/A'),
                    'upc': product.get('upc', 'N/A'),
                    'description': product.get('description', 'N/A'),
                    'brand': product.get('brand', 'N/A'),
                    'categories': product.get('categories', ['N/A']),
                    'countryOrigin': product.get('countryOrigin', 'N/A'),
                    'temperature': product.get('temperature', 'N/A'),
                    'images': product.get('images', []),
                    'items': []
                }

                # Process items with default values
                for item in product.get('items', []):
                    item_info = {
                        'itemId': item.get('itemId', 'N/A'),
                        'price': {
                            'regular': item.get('price', {}).get('regular', 0.0),
                            'promo': item.get('price', {}).get('promo', None)
                        },
                        'size': item.get('size', 'N/A'),
                        'soldBy': item.get('soldBy', 'N/A'),
                        'inventory': item.get('inventory', {
                            'status': 'N/A'
                        }),
                        'fulfillment': item.get('fulfillment', {
                            'status': 'N/A'
                        })
                    }
                    product_info['items'].append(item_info)

                # If no items were found, add a default item
                if not product_info['items']:
                    product_info['items'].append({
                        'itemId': 'N/A',
                        'price': {
                            'regular': 0.0,
                            'promo': None
                        },
                        'size': 'N/A',
                        'soldBy': 'N/A',
                        'inventory': {
                            'status': 'N/A'
                        },
                        'fulfillment': {
                            'status': 'N/A'
                        }
                    })

                products.append(product_info)

            except Exception as product_error:
                print(f"Error processing product: {str(product_error)}")
                # Add minimal product info if there's an error
                products.append({
                    'productId': search_product.get('productId', 'N/A'),
                    'upc': 'N/A',
                    'description': search_product.get('description', 'N/A'),
                    'brand': search_product.get('brand', 'N/A'),
                    'categories': ['N/A'],
                    'countryOrigin': 'N/A',
                    'temperature': 'N/A',
                    'images': [],
                    'items': [{
                        'itemId': 'N/A',
                        'price': {
                            'regular': 0.0,
                            'promo': None
                        },
                        'size': 'N/A',
                        'soldBy': 'N/A',
                        'inventory': {
                            'status': 'N/A'
                        },
                        'fulfillment': {
                            'status': 'N/A'
                        }
                    }]
                })

        return jsonify({
            'query': query,
            'products': products
        })

    except Exception as e:
        print(f"Error searching Kroger products: {str(e)}")
        # Return minimal response even on error
        return jsonify({
            'query': query,
            'products': [],
            'error': str(e)
        })

def kroger_recipe_ingredients_info(recipe_id):
    """
    Get Kroger product details for all ingredients in a recipe.
    """
    from app.functions.recipe_functions import get_recipe_ingredients  # Avoid circular import

    ingredients, error = get_recipe_ingredients(recipe_id)
    if error:
        return jsonify({'error': error}), 500

    # Get Kroger access token
    access_token = get_access_token()
    if not access_token:
        return jsonify({'error': 'Failed to get Kroger access token'}), 500

    kroger_ingredients = []
    total_price = 0

    for ingredient in ingredients["ingredients"]:
        if ingredient["name"]:
            new_ingredient_name = ingredient["name"]
            # Remove any variation of "additional toppings: "
            if "additional toppings: " in new_ingredient_name.lower():
                new_ingredient_name = new_ingredient_name.split("additional toppings: ")[-1]
                prefix = new_ingredient_name.split("additional toppings: ")[0]
                if prefix and prefix.strip():
                    new_ingredient_name = prefix.strip() + " " + new_ingredient_name

            # Get Kroger product details for this ingredient
            product_details = get_kroger_product_details(new_ingredient_name, access_token)

            if product_details:
                kroger_ingredients.append(product_details)
                # Add the price of the first item variant to the total
                if product_details['items'] and 'price' in product_details['items'][0]:
                    total_price += product_details['items'][0]['price'].get('regular', 0)

    return jsonify({
        'ingredients': kroger_ingredients,
        'totalPrice': round(total_price, 2)
    })