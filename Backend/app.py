from flask import Flask, jsonify, request, render_template
from kroger import get_products_from_list
import os
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("API_KEY")

# Helper function to fetch ingredients
def get_ingredients_from_recipe(recipe_id):
    """Fetch ingredients for a recipe by ID using the Spoonacular API."""
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/ingredientWidget.json"
    headers = {"Accept": "application/json"}
    params = {"apiKey": API_KEY}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        # Extract ingredient names
        return [ingredient["name"] for ingredient in data["ingredients"]]
    else:
        raise Exception(f"Failed to fetch ingredients: {response.status_code}, {response.text}")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/recipes")
def search_recipes():
    """Search for recipes by query."""
    query = request.args.get("query", "pasta")  # Default to 'pasta'
    url = f"https://api.spoonacular.com/recipes/complexSearch"
    params = {"query": query, "apiKey": API_KEY}

    response = requests.get(url, params=params)
    return jsonify(response.json() if response.status_code == 200 else {"error": "Failed to fetch recipes"})

@app.route("/recipe/<int:recipe_id>/ingredients")
def recipe_ingredients(recipe_id):
    """Fetch ingredients for a recipe and search for related products."""
    try:
        # Step 1: Fetch ingredients
        ingredients = get_ingredients_from_recipe(recipe_id)

        # Step 2: Search products for ingredients
        products = get_products_from_list(ingredients)

        return jsonify({"ingredients": ingredients, "products": products})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
