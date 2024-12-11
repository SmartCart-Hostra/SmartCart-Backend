import requests
from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

def get_access_token():
    """Get access token from Kroger API"""
    url = "https://api.kroger.com/v1/connect/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "client_credentials", "scope": "product.compact"}
    response = requests.post(url, headers=headers, data=data, auth=(CLIENT_ID, CLIENT_SECRET))
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Failed to get access token: {response.status_code}, {response.text}")

def search_products(query, access_token, location_id=None):
    """Search for products using Kroger API."""
    base_url = "https://api.kroger.com/v1/products"
    params = {
        "filter.term": query,
        "filter.limit": 5
    }
    if location_id:
        params["filter.locationId"] = location_id

    headers = {"Accept": "application/json", "Authorization": f"Bearer {access_token}"}
    response = requests.get(base_url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to search products: {response.status_code}, {response.text}")


def get_first_product(query):
    """Get the first product from the search results"""
    try:
        # Get the access token
        access_token = get_access_token()

        # Search for products
        result = search_products(query, access_token)

        # Extract the first product from the data
        first_product = result["data"][0] if "data" in result and len(result["data"]) > 0 else None
        print(first_product)
        return first_product
    except Exception as e:
        print("Error:", e)
        return None

def get_products_from_list(queries, location_id):
    """Search for multiple products and return a list of the first products for each query."""
    try:
        # Get the access token
        access_token = get_access_token()

        # List to store the results
        products = []

        # Loop through each query and get the first product
        for query in queries:
            print(f"Searching for: {query}")
            result = search_products(query, access_token, location_id)
            first_product = result["data"][0] if "data" in result and len(result["data"]) > 0 else None

            if first_product:
                #print("Product JSON:", first_product)
                products.append(first_product)
            else:
                print(f"No product found for query: {query}")

        return products
    except Exception as e:
        print("Error:", e)
        return []
