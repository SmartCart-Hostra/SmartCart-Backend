from flask import Flask, request, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import jwt
import datetime
import os
from pymongo import MongoClient
import smtplib
from email.mime.text import MIMEText
import random
import string


import aiohttp
from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv
import os
import requests

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

# Access the API_KEY from environment variables
api_key = os.getenv("API_KEY")

# Kroger API credentials
CLIENT_ID = os.getenv('KROGER_CLIENT_ID')
CLIENT_SECRET = os.getenv('KROGER_CLIENT_SECRET')

accessTokenKroger = None
LOCATION_ID = '01400943'



# MongoDB Atlas setup
MONGODB_URI = os.getenv('MONGODB_URI')

try:
    client = MongoClient(MONGODB_URI)
    # Ping the database to verify connection
    client.admin.command('ping')
    print("Successfully connected to MongoDB!")
    db = client['user_auth_db']  # You can change the database name
    users_collection = db['users']
    tokens_collection = db['tokens']
except Exception as e:
    print(f"Error connecting to MongoDB Atlas: {e}")
    raise

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = os.getenv("EMAIL_USERNAME")
SMTP_PASSWORD = os.getenv("EMAIL_PASSWORD")

# JWT configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    JWT_SECRET_KEY = ''.join(random.choices(string.ascii_letters + string.digits, k=32))

def generate_2fa_token():
    """Generate a 6-digit 2FA token"""
    return ''.join(random.choices(string.digits, k=6))

def send_2fa_email(email, token):
    """Send 2FA token via email"""
    msg = MIMEText(f'Your verification code is: {token}')
    msg['Subject'] = '2FA Verification Code'
    msg['From'] = SMTP_USERNAME
    msg['To'] = email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def token_required(f):
    """Decorator for protected routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('token')
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
            current_user = users_collection.find_one({'email': data['email']})
            if not current_user:
                return jsonify({'message': 'Invalid token'}), 401
        except:
            return jsonify({'message': 'Invalid token'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing required fields'}), 400

    # Check if user already exists
    if users_collection.find_one({'email': data['email']}):
        return jsonify({'message': 'User already exists'}), 409

    # Hash password and create user
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    new_user = {
        'email': data['email'],
        'password': hashed_password,
        'is_verified': False,
        'created_at': datetime.datetime.utcnow()
    }
    
    users_collection.insert_one(new_user)
    
    # Generate and send 2FA token
    token = generate_2fa_token()
    tokens_collection.insert_one({
        'email': data['email'],
        'token': token,
        'created_at': datetime.datetime.utcnow()
    })
    
    if send_2fa_email(data['email'], token):
        return jsonify({'message': 'User created. Please verify your email'}), 201
    else:
        return jsonify({'message': 'Error sending verification email'}), 500

@app.route('/verify-2fa', methods=['POST'])
def verify_2fa():
    data = request.json
    
    if not data or not data.get('email') or not data.get('token'):
        return jsonify({'message': 'Missing required fields'}), 400

    stored_token = tokens_collection.find_one({
        'email': data['email'],
        'token': data['token'],
        'created_at': {'$gt': datetime.datetime.utcnow() - datetime.timedelta(minutes=10)}
    })

    if not stored_token:
        return jsonify({'message': 'Invalid or expired token'}), 401

    # Update user verification status
    users_collection.update_one(
        {'email': data['email']},
        {'$set': {'is_verified': True}}
    )
    
    # Clean up used token
    tokens_collection.delete_one({'_id': stored_token['_id']})
    
    return jsonify({'message': 'Email verified successfully'}), 200

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing required fields'}), 400

    user = users_collection.find_one({'email': data['email']})
    
    if not user or not check_password_hash(user['password'], data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401

    if not user['is_verified']:
        return jsonify({'message': 'Please verify your email first'}), 403

    # Generate and send 2FA token for login
    token = generate_2fa_token()
    tokens_collection.insert_one({
        'email': data['email'],
        'token': token,
        'created_at': datetime.datetime.utcnow()
    })
    
    if send_2fa_email(data['email'], token):
        return jsonify({'message': 'Please check your email for 2FA code'}), 200
    else:
        return jsonify({'message': 'Error sending 2FA code'}), 500

@app.route('/login-verify', methods=['POST'])
def login_verify():
    data = request.json
    
    if not data or not data.get('email') or not data.get('token'):
        return jsonify({'message': 'Missing required fields'}), 400

    stored_token = tokens_collection.find_one({
        'email': data['email'],
        'token': data['token'],
        'created_at': {'$gt': datetime.datetime.utcnow() - datetime.timedelta(minutes=10)}
    })

    if not stored_token:
        return jsonify({'message': 'Invalid or expired token'}), 401

    # Generate JWT token
    token = jwt.encode({
        'email': data['email'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, JWT_SECRET_KEY)

    # Clean up used token
    tokens_collection.delete_one({'_id': stored_token['_id']})
    
    # Create response with httpOnly cookie
    response = make_response(jsonify({'message': 'Login successful'}))
    response.set_cookie(
        'token',
        token,
        httponly=True,
        secure=True,  # Enable in production with HTTPS
        samesite='Strict',
        max_age=7 * 24 * 60 * 60  # 7 days
    )
    
    return response

@app.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    response = make_response(jsonify({'message': 'Logout successful'}))
    response.delete_cookie('token')
    return response

# Example protected route
@app.route('/protected', methods=['GET'])
@token_required
def protected_route(current_user):
    return jsonify({'message': f'Hello {current_user["email"]}!'})






def get_access_token():
    """Get access token from Kroger API"""
    url = "https://api.kroger.com/v1/connect/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "client_credentials", "scope": "product.compact"}
    response = requests.post(url, headers=headers, data=data, auth=(CLIENT_ID, CLIENT_SECRET))
    return response.json()["access_token"]

def search_products(query, access_token):
    """Search for products using Kroger API"""
    
    url = f"https://api.kroger.com/v1/products?filter.term={query}&filter.limit=5"
    headers = {"Accept": "application/json", "Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    return jsonify(response.json())

@app.route("/recipes")
def recipes():
    """
    Route to get recipes based on a query parameter.
    """
    query = request.args.get("query")
    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {
        "query": query,
        "apiKey": api_key
    }
    response = requests.get(url, params=params)
    return jsonify(response.json())

def get_recipe_ingredients(recipe_id):
    """Helper function to get recipe ingredients from Spoonacular"""
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/ingredientWidget.json"
    params = {
        "apiKey": api_key
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        cleaned_ingredients = []
        
        for ingredient in data.get('ingredients', []):
            metric = ingredient.get('amount', {}).get('metric', {})
            cleaned_ingredient = {
                'name': ingredient.get('name'),
                'image': ingredient.get('image'),
                'amount': metric.get('value'),
                'unit': metric.get('unit')
            }
            cleaned_ingredients.append(cleaned_ingredient)
            
        return {'ingredients': cleaned_ingredients}, None
        
    except Exception as e:
        return None, str(e)

@app.route("/recipe/<int:recipe_id>")
def recipe_ingredients(recipe_id):
    ingredients, error = get_recipe_ingredients(recipe_id)
    if error:
        return jsonify({'error': error}), 500
    return jsonify(ingredients)

@app.route("/kroger/recipe/<int:recipe_id>")
def kroger_recipe_ingredients_info(recipe_id):
    ingredients, error = get_recipe_ingredients(recipe_id)
    if error:
        return jsonify({'error': error}), 500
    
    # Get Kroger access token
    access_token = get_access_token()
    if not access_token:
        return jsonify({'error': 'Failed to get Kroger access token'}), 500

    kroger_ingredients = []
    total_price = 0

    def get_kroger_product_details(ingredient_name):
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

    for ingredient in ingredients["ingredients"]:
        if ingredient["name"]:
            newIngredientName = ingredient["name"]
            # Remove any variation of "additional toppings: "
            if "additional toppings: " in newIngredientName.lower():
                newIngredientName = newIngredientName.split("additional toppings: ")[-1]
                prefix = newIngredientName.split("additional toppings: ")[0]
                if prefix and prefix.strip():
                    newIngredientName = prefix.strip() + " " + newIngredientName
            
            # Get Kroger product details for this ingredient
            product_details = get_kroger_product_details(newIngredientName)
            
            if product_details:
                kroger_ingredients.append(product_details)
                # Add the price of the first item variant to the total
                if product_details['items'] and 'price' in product_details['items'][0]:
                    total_price += product_details['items'][0]['price'].get('regular', 0)

    return jsonify({
        'ingredients': kroger_ingredients,
        'totalPrice': round(total_price, 2)
    })

@app.route("/kroger")
def kroger_search():
    query = request.args.get('query')
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
from app.routes.recipe_routes import recipe_routes
app.register_blueprint(recipe_routes)  


if __name__ == "__main__":
    # accessTokenKroger = get_access_token()
    app.run(debug=True)
