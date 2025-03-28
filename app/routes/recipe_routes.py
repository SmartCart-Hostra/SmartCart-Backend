import os
import requests
import json
from flask import Blueprint, jsonify, request
from app.functions.auth_functions import token_required
from app.functions.preference_functions import NUTRITION_GOALS
from app.functions.recipe_functions import fetch_recipe_detail
from dotenv import load_dotenv
from pathlib import Path

recipe_routes = Blueprint('recipe_routes', __name__)

# Force load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / '.env', override=True)

API_KEY = os.getenv("API_KEY")
print(f"🔑 Recipe Routes API Key: {API_KEY}")

@recipe_routes.route("/recipedetail/<int:recipe_id>", methods=['GET'])
@token_required
def recipe_detail_get(current_user, recipe_id):
    """
    Returns detailed information about a recipe.
    """
    data, status_code = fetch_recipe_detail(recipe_id)

    if "error" in data:
        return jsonify(data), status_code

    return jsonify(data), status_code

@recipe_routes.route('/randomrecipe', methods=['GET'])
@token_required
def get_random_recipes(current_user):
    try:
        from app import user_preferences_collection
        prefs = user_preferences_collection.find_one({"email": current_user["email"]}) or {}

        # Get number of recipes to fetch (default: 5)
        limit = request.args.get("limit", 5, type=int)
        max_attempts = 1  # Prevent infinite loop by retrying only 3 times
        attempt = 0
        filtered_recipes = []

        while len(filtered_recipes) < limit and attempt < max_attempts:
            attempt += 1  # Keep track of attempts
            params = {
                "apiKey": API_KEY,
                "number": (limit - len(filtered_recipes)) * 2,  # Fetch more if needed
                "limitLicense": "true"
            }

            # ✅ Convert diet preferences to lowercase
            diet_tags = [d.lower() for d in prefs.get("diets", [])]

            # ✅ Convert cuisine preferences to lowercase
            cuisine_tags = [c.lower() for c in prefs.get("cuisines", [])]

            # ✅ Combine diet & cuisine into the `tags` parameter
            if diet_tags or cuisine_tags:
                params["tags"] = ",".join(diet_tags + cuisine_tags)

            # ✅ Print API request URL for debugging
            print("Fetching from Spoonacular API with URL:")
            print(f"https://api.spoonacular.com/recipes/random?{params}")

            response = requests.get(
                "https://api.spoonacular.com/recipes/random",
                params=params
            )
            response.raise_for_status()
            data = response.json()

            # ✅ Print raw API response for debugging
            print("\n🔍 Raw API Response:")
            print(json.dumps(data, indent=2))  # Pretty print JSON

            # ✅ Filter out recipes containing allergens
            allergies = [a.lower() for a in prefs.get("intolerances", [])]  # Convert allergies to lowercase
            removed_due_to_allergens = 0
            for recipe in data.get("recipes", []):
                if "extendedIngredients" in recipe:
                    ingredients = [ingredient["name"].lower() for ingredient in recipe["extendedIngredients"]]
                    if any(allergy in ingredients for allergy in allergies):
                        removed_due_to_allergens += 1
                        continue  # Skip this recipe if it contains an allergen

                # ✅ Apply nutrition filters manually
                nutrition_goals = prefs.get("nutrition_goals", {})
                if "nutrition" in recipe:
                    if any(
                        ("minCalories" in nutrition_goals and recipe["nutrition"]["nutrients"][0]["amount"] < nutrition_goals["minCalories"]) or
                        ("maxCalories" in nutrition_goals and recipe["nutrition"]["nutrients"][0]["amount"] > nutrition_goals["maxCalories"]) or
                        ("minProtein" in nutrition_goals and recipe["nutrition"]["nutrients"][1]["amount"] < nutrition_goals["minProtein"]) or
                        ("maxProtein" in nutrition_goals and recipe["nutrition"]["nutrients"][1]["amount"] > nutrition_goals["maxProtein"])
                    ):
                        continue  # Skip recipe if it doesn't match nutrition goals

                filtered_recipes.append(recipe)

                # Stop once we have enough recipes
                if len(filtered_recipes) >= limit:
                    break

        # ✅ Print removed recipe count for debugging
        print(f"\n🚨 Removed {removed_due_to_allergens} recipes due to allergies")
        print(f"✅ Final recipe count: {len(filtered_recipes)} / {limit}")

        return jsonify({
            "results": filtered_recipes,
            "meta": {
                "count": len(filtered_recipes),
                "limit": limit,
                "attempts": attempt,
                "removed_due_to_allergens": removed_due_to_allergens,
                "applied_filters": {
                    "diet": diet_tags,
                    "intolerances": allergies,
                    "cuisine": cuisine_tags,
                    "nutrition_goals": prefs.get("nutrition_goals", {})
                }
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

        # Add price range filter
        price_range = request.args.get("price_range")
        if price_range:
            if price_range == "low":
                params["maxPrice"] = 10
            elif price_range == "mid":
                params["minPrice"] = 10
                params["maxPrice"] = 30
            elif price_range == "expensive":
                params["minPrice"] = 30

        # Add time filter
        time_range = request.args.get("time_range")
        if time_range:
            if time_range == "quick":
                params["maxReadyTime"] = 15
            elif time_range == "medium":
                params["minReadyTime"] = 15
                params["maxReadyTime"] = 30
            elif time_range == "long":
                params["minReadyTime"] = 30

        # Add meal type filter
        meal_type = request.args.get("meal_type")
        if meal_type:
            params["type"] = meal_type

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
                    "nutrition_goals": prefs.get('nutrition_goals', []),
                    "price_range": price_range,
                    "time_range": time_range,
                    "meal_type": meal_type
                }
            }
        }), 200

    except requests.exceptions.HTTPError as e:
        return jsonify({"error": f"Spoonacular API error: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500
