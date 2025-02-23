import os
import requests
from flask import Blueprint, jsonify, request, current_app
from app.functions.auth_functions import token_required
from app.functions.preference_functions import NUTRITION_GOALS

recipe_routes = Blueprint('recipe_routes', __name__)

API_KEY = os.getenv("API_KEY")

@recipe_routes.route('/randomrecipe', methods=['GET'])
@token_required
def get_random_recipes(current_user):
    try:
        from app import user_preferences_collection
        prefs = user_preferences_collection.find_one(
            {"email": current_user["email"]}
        ) or {}

        # Define some common keywords for random recipe suggestions
        random_keywords = ["chicken", "pasta", "salad", "soup", "dessert", "vegetarian", "seafood", "beef"]

        import random
        query = random.choice(random_keywords)  # Pick a random keyword

        # Get pagination parameters from request (default: page=1, limit=5)
        page = request.args.get("page", 1, type=int)  # Page number (1-based)
        limit = request.args.get("limit", 5, type=int)  # Results per page
        offset = (page - 1) * limit  # Convert page number to offset

        params = {
            "query": query,
            "apiKey": API_KEY,
            "number": limit,  # Recipes per page
            "offset": offset  # Start position for pagination
        }

        # Add existing preference parameters
        if prefs.get('diets'):
            params["diet"] = ",".join([d.lower() for d in prefs['diets']])
        if prefs.get('intolerances'):
            params["intolerances"] = ",".join(prefs['intolerances'])
        if prefs.get('cuisines'):
            params["cuisine"] = ",".join(prefs['cuisines'])

        # Add nutrition goal parameters
        if prefs.get('nutrition_goals'):
            nutrition_params = {}
            for goal in prefs['nutrition_goals']:
                goal_config = next((g for g in NUTRITION_GOALS.values() if g['name'] == goal), None)
                if goal_config:
                    nutrition_params.update(goal_config['params'])

            params.update(nutrition_params)

        response = requests.get(
            "https://api.spoonacular.com/recipes/complexSearch",
            params=params
        )
        response.raise_for_status()
        data = response.json()

        return jsonify({
            "results": data.get("results", []),
            "meta": {
                "count": len(data.get("results", [])),
                "total_results": data.get("totalResults", 0),  # Spoonacular provides total results
                "page": page,
                "limit": limit,
                "next_page": page + 1 if offset + limit < data.get("totalResults", 0) else None,
                "search_query": query
            }
        }), 200

    except requests.exceptions.HTTPError as e:
        return jsonify({"error": f"Spoonacular API error: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@recipe_routes.route('/recipes', methods=['GET'])
@token_required
def get_recipes(current_user):
    try:
        query = request.args.get("query")
        from app import user_preferences_collection
        prefs = user_preferences_collection.find_one(
            {"email": current_user["email"]}
        ) or {}

        # Get pagination parameters from request (default: page=1, limit=10)
        page = request.args.get("page", 1, type=int)  # Page number (1-based)
        limit = request.args.get("limit", 10, type=int)  # Results per page
        offset = (page - 1) * limit  # Convert page number to offset

        params = {
            "query": query,
            "apiKey": API_KEY,
            "number": limit,  # Recipes per page
            "offset": offset  # Start position for pagination
        }

        # Add existing preference parameters
        if prefs.get('diets'):
            params["diet"] = ",".join([d.lower() for d in prefs['diets']])
        if prefs.get('intolerances'):
            params["intolerances"] = ",".join(prefs['intolerances'])
        if prefs.get('cuisines'):
            params["cuisine"] = ",".join(prefs['cuisines'])

        # Add nutrition goal parameters
        if prefs.get('nutrition_goals'):
            nutrition_params = {}
            for goal in prefs['nutrition_goals']:
                goal_config = next((g for g in NUTRITION_GOALS.values() if g['name'] == goal), None)
                if goal_config:
                    nutrition_params.update(goal_config['params'])

            params.update(nutrition_params)

        response = requests.get(
            "https://api.spoonacular.com/recipes/complexSearch",
            params=params
        )
        response.raise_for_status()
        data = response.json()

        return jsonify({
            "results": data.get("results", []),
            "meta": {
                "count": len(data.get("results", [])),
                "total_results": data.get("totalResults", 0),  # Spoonacular provides total results
                "page": page,
                "limit": limit,
                "next_page": page + 1 if offset + limit < data.get("totalResults", 0) else None,
                "filters": {
                    "diets": prefs.get('diets', []),
                    "intolerances": prefs.get('intolerances', []),
                    "cuisines": prefs.get('cuisines', []),
                    "nutrition_goals": prefs.get('nutrition_goals', [])
                }
            }
        }), 200

    except requests.exceptions.HTTPError as e:
        return jsonify({"error": f"Spoonacular API error: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500
