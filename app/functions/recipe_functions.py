import os
import requests
from flask import jsonify, request
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Spoonacular API key
SPOONACULAR_API_KEY = os.getenv("API_KEY")

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