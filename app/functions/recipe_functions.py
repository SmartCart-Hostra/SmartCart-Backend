import os
import requests
from flask import jsonify, request
from dotenv import load_dotenv
from pathlib import Path

# Force load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / '.env', override=True)

# Spoonacular API key
SPOONACULAR_API_KEY = os.getenv("API_KEY")
print(f"🔑 Recipe Functions API Key: {SPOONACULAR_API_KEY}")

def recipes():
    """
    Get recipes based on a query parameter.
    """
    query = request.args.get("query")
    if not query:
        return jsonify({'error': 'Missing query parameter'}), 400

    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {
        "query": query,
        "apiKey": SPOONACULAR_API_KEY
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error fetching recipes: {e}")
        return jsonify({'error': 'Failed to fetch recipes'}), 500

def get_recipe_ingredients(recipe_id):
    """
    Get the ingredients for a specific recipe from Spoonacular API.
    """
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/ingredientWidget.json"
    params = {
        "apiKey": SPOONACULAR_API_KEY
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

    except requests.exceptions.RequestException as e:
        print(f"Error fetching recipe ingredients: {e}")
        return None, str(e)

def recipe_ingredients(recipe_id):
    """
    Handle the route for fetching recipe ingredients.
    """
    ingredients, error = get_recipe_ingredients(recipe_id)
    if error:
        return jsonify({'error': error}), 500
    return jsonify(ingredients)

def fetch_recipe_detail(recipe_id):
    """
    Fetches detailed information about a recipe using Spoonacular API.
    """
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {"apiKey": SPOONACULAR_API_KEY}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json(), 200
    except requests.exceptions.RequestException as e:
        print(f"Error fetching recipe details: {e}")
        return {"error": "Failed to fetch recipe details"}, 500

def find_recipes_by_ingredients(ingredients, number=10, limit_license=True, ranking=1, ignore_pantry=False):
    """
    Find recipes that use the provided ingredients using Spoonacular API.
    
    Args:
        ingredients (list or str): List of ingredients or comma-separated string
        number (int): Maximum number of recipes to return
        limit_license (bool): Whether to limit results to recipes with licenses
        ranking (int): Whether to rank by 1=maximize used ingredients, 2=minimize missing ingredients
        ignore_pantry (bool): Whether to ignore pantry ingredients like salt, pepper, etc.
    
    Returns:
        tuple: (data, status_code)
    """
    # Ensure ingredients is a comma-separated string
    if isinstance(ingredients, list):
        ingredients = ','.join(ingredients)
    
    url = "https://api.spoonacular.com/recipes/findByIngredients"
    params = {
        "ingredients": ingredients,
        "number": number,
        "apiKey": SPOONACULAR_API_KEY,
        "limitLicense": str(limit_license).lower(),
        "ranking": ranking,
        "ignorePantry": str(ignore_pantry).lower()
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json(), 200
    except requests.exceptions.RequestException as e:
        print(f"Error finding recipes by ingredients: {e}")
        return {"error": "Failed to find recipes by ingredients"}, 500