import os
import requests
from flask import Blueprint, jsonify, request, current_app
from app.functions.auth_functions import token_required
from app.functions.preference_functions import NUTRITION_GOALS

recipe_routes = Blueprint('recipe_routes', __name__)

API_KEY = os.getenv("API_KEY")

@recipe_routes.route('/recipes', methods=['GET'])
@token_required
def get_recipes(current_user):
    try:
        query = request.args.get("query")
        prefs = current_app.user_preferences_collection.find_one(
            {"email": current_user["email"]}
        ) or {}

        params = {
            "query": query,
            "apiKey": API_KEY,
            "number": 10
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
            
            # Apply nutrition parameters to the API request
            params.update(nutrition_params)

        response = requests.get(
            "https://api.spoonacular.com/recipes/complexSearch",
            params=params
        )
        response.raise_for_status()

        return jsonify({
            "results": response.json().get("results", []),
            "meta": {
                "count": len(response.json().get("results", [])),
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