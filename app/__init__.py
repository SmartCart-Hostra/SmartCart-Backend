from flask import Flask
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from app.config import SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, JWT_SECRET_KEY

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

# MongoDB Atlas setup
MONGODB_URI = os.getenv('MONGODB_URI')

try:
    client = MongoClient(MONGODB_URI)
    client.admin.command('ping')
    print("Successfully connected to MongoDB!")
    db = client['user_auth_db']  # You can change the database name
    users_collection = db['users']
    tokens_collection = db['tokens']
    user_preferences_collection = db['user_preferences']
    saved_recipes_collection = db['saved_recipes']
    # New collections for cart and order functionality
    cart_items_collection = db['cart_items']
    orders_collection = db['orders']
except Exception as e:
    print(f"Error connecting to MongoDB Atlas: {e}")
    raise

# Import routes
from app.routes.auth_routes import auth_routes
from app.routes.kroger_routes import kroger_routes
from app.routes.recipe_routes import recipe_routes
from app.routes.preference_routes import preference_routes
from app.routes.saved_recipe_routes import saved_recipe_routes
# Import new route blueprints
from app.routes.cart_routes import cart_routes
from app.routes.order_routes import order_routes

# Register blueprints
app.register_blueprint(auth_routes)
app.register_blueprint(kroger_routes)
app.register_blueprint(recipe_routes)
app.register_blueprint(preference_routes)
app.register_blueprint(saved_recipe_routes)
# Register new blueprints
app.register_blueprint(cart_routes)
app.register_blueprint(order_routes)

# Set JWT secret key
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY