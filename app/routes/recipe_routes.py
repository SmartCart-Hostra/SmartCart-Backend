import os
import requests
import json
from flask import Blueprint, jsonify, request
from dotenv import load_dotenv
from pathlib import Path

from app.functions.auth_functions import token_required
from app.functions.preference_functions import NUTRITION_GOALS
from app.functions.recipe_functions import fetch_recipe_detail, find_recipes_by_ingredients
from app.functions.smart_recommendations import build_user_profile, score_recipe

recipe_routes = Blueprint('recipe_routes', __name__)

# Force load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / '.env', override=True)

API_KEY = os.getenv("API_KEY")
print(f"🔑 Recipe Routes API Key: {API_KEY}")

# ======= RECIPE DETAIL ROUTE =======
@recipe_routes.route("/recipedetail/<int:recipe_id>", methods=['GET'])
@token_required
def recipe_detail_get(current_user, recipe_id):
    data, status_code = fetch_recipe_detail(recipe_id)
    if "error" in data:
        return jsonify(data), status_code
    return jsonify(data), status_code

# ======= RANDOM RECIPE GENERATION (FILTERED) =======
@recipe_routes.route('/randomrecipe', methods=['GET'])
@token_required
def get_random_recipes(current_user):
    try:
        from app import user_preferences_collection
        prefs = user_preferences_collection.find_one({"email": current_user["email"]}) or {}

        limit = request.args.get("limit", 5, type=int)
        max_attempts = 1
        attempt = 0
        filtered_recipes = []

        while len(filtered_recipes) < limit and attempt < max_attempts:
            attempt += 1
            params = {
                "apiKey": API_KEY,
                "number": (limit - len(filtered_recipes)) * 2,
                "limitLicense": "true"
            }

            diet_tags = [d.lower() for d in prefs.get("diets", [])]
            cuisine_tags = [c.lower() for c in prefs.get("cuisines", [])]
            if diet_tags or cuisine_tags:
                params["tags"] = ",".join(diet_tags + cuisine_tags)

            response = requests.get(
                "https://api.spoonacular.com/recipes/random",
                params=params
            )
            response.raise_for_status()
            data = response.json()

            allergies = [a.lower() for a in prefs.get("intolerances", [])]
            removed_due_to_allergens = 0
            for recipe in data.get("recipes", []):
                if "extendedIngredients" in recipe:
                    ingredients = [ingredient["name"].lower() for ingredient in recipe["extendedIngredients"]]
                    if any(allergy in ingredients for allergy in allergies):
                        removed_due_to_allergens += 1
                        continue

                nutrition_goals = prefs.get("nutrition_goals", {})
                if "nutrition" in recipe:
                    if any(
                        ("minCalories" in nutrition_goals and recipe["nutrition"]["nutrients"][0]["amount"] < nutrition_goals["minCalories"]) or
                        ("maxCalories" in nutrition_goals and recipe["nutrition"]["nutrients"][0]["amount"] > nutrition_goals["maxCalories"]) or
                        ("minProtein" in nutrition_goals and recipe["nutrition"]["nutrients"][1]["amount"] < nutrition_goals["minProtein"]) or
                        ("maxProtein" in nutrition_goals and recipe["nutrition"]["nutrients"][1]["amount"] > nutrition_goals["maxProtein"])
                    ):
                        continue

                filtered_recipes.append(recipe)
                if len(filtered_recipes) >= limit:
                    break

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

# ======= SEARCH RECIPES ROUTE =======
@recipe_routes.route('/recipes', methods=['GET'])
@token_required
def get_recipes(current_user):
    try:
        query = request.args.get("query")
        from app import user_preferences_collection
        prefs = user_preferences_collection.find_one({"email": current_user["email"]}) or {}

        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 10, type=int)
        offset = (page - 1) * limit

        params = {
            "query": query,
            "apiKey": API_KEY,
            "number": limit * 2,
            "offset": offset
        }

        if prefs.get('diets'):
            params["diet"] = ",".join([d.lower() for d in prefs['diets']])
        if prefs.get('intolerances'):
            params["intolerances"] = ",".join(prefs['intolerances'])
        if prefs.get('cuisines'):
            params["cuisine"] = ",".join(prefs['cuisines'])

        if prefs.get('nutrition_goals'):
            nutrition_params = {}
            for goal in prefs['nutrition_goals']:
                goal_config = next((g for g in NUTRITION_GOALS.values() if g['name'] == goal), None)
                if goal_config:
                    nutrition_params.update(goal_config['params'])
            params.update(nutrition_params)

        price_range = request.args.get("price_range")
        time_range = request.args.get("time_range")
        meal_type = request.args.get("meal_type")

        if time_range == "quick":
            params["maxReadyTime"] = 15
        elif time_range == "medium":
            params["maxReadyTime"] = 30
        elif time_range == "long":
            params["maxReadyTime"] = 90

        meal_type_map = {
            "breakfast": "breakfast",
            "lunch": "main course",
            "dinner": "main course",
            "main course": "main course",
            "appetizer": "appetizer",
            "dessert": "dessert"
        }
        mapped_meal_type = meal_type_map.get(meal_type.lower()) if meal_type else None
        if mapped_meal_type:
            params["type"] = mapped_meal_type

        response = requests.get(
            "https://api.spoonacular.com/recipes/complexSearch",
            params=params
        )
        response.raise_for_status()
        data = response.json()
        all_results = data.get("results", [])

        filtered_results = []
        for recipe in all_results:
            price = recipe.get("pricePerServing", 0) / 100
            if price_range == "low" and price > 10:
                continue
            elif price_range == "mid" and not (10 < price <= 30):
                continue
            elif price_range == "expensive" and price <= 30:
                continue

            filtered_results.append(recipe)
            if len(filtered_results) >= limit:
                break

        return jsonify({
            "results": filtered_results,
            "meta": {
                "count": len(filtered_results),
                "total_results": data.get("totalResults", 0),
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

# ======= RECIPES BY INGREDIENTS ROUTE =======
@recipe_routes.route('/recipes/by-ingredients', methods=['GET'])
@token_required
def recipes_by_ingredients(current_user):
    try:
        ingredients = request.args.get("ingredients")
        if not ingredients:
            return jsonify({"error": "Missing ingredients parameter"}), 400

        number = request.args.get("number", 10, type=int)
        limit_license = request.args.get("limitLicense", "true").lower() == "true"
        ranking = request.args.get("ranking", 1, type=int)
        ignore_pantry = request.args.get("ignorePantry", "false").lower() == "true"

        data, status_code = find_recipes_by_ingredients(
            ingredients=ingredients,
            number=number,
            limit_license=limit_license,
            ranking=ranking,
            ignore_pantry=ignore_pantry
        )

        if "error" in data:
            return jsonify(data), status_code

        return jsonify({
            "results": data,
            "meta": {
                "count": len(data),
                "ingredients": ingredients.split(',')
            }
        }), status_code

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# ======= SMART RECOMMENDATIONS ROUTE (✨) =======
@recipe_routes.route('/smartfeed', methods=['POST'])
@token_required
def smart_feed(current_user):
    try:
        from app import user_preferences_collection
        prefs = user_preferences_collection.find_one({"email": current_user["email"]}) or {}

        data = request.get_json()
        saved_recipes = data.get("savedRecipes", [])

        if len(saved_recipes) < 3:
            return jsonify({
                "showSmartRecommendations": False,
                "message": "Save at least 3 recipes to unlock Smart Recommendations."
            })

        profile = build_user_profile(saved_recipes)
        preferences = {
            "diet": prefs.get("diets", [None])[0],
            "cuisine": prefs.get("cuisines", [None])[0],
            "excludeIngredients": prefs.get("intolerances", [])
        }

        params = {
            "apiKey": API_KEY,
            "number": 10,
            "limitLicense": "true"
        }

        spoonacular_response = requests.get(
            "https://api.spoonacular.com/recipes/random",
            params=params
        )
        spoonacular_response.raise_for_status()
        spoonacular_data = spoonacular_response.json()
        new_recipes = spoonacular_data.get("recipes", [])

        smart_results = []
        for recipe in new_recipes:
            tags = recipe.get("dishTypes", [])
            ingredients = [ing["name"] for ing in recipe.get("extendedIngredients", [])]

            recipe["tags"] = tags
            recipe["ingredients"] = ingredients

            score = score_recipe(recipe, profile, preferences)
            recipe["match_score"] = score
            smart_results.append(recipe)

        top_matches = sorted(smart_results, key=lambda r: r["match_score"], reverse=True)[:5]

        return jsonify({
            "showSmartRecommendations": True,
            "smartRecommendations": top_matches
        })

    except Exception as e:
        print("SmartFeed Error:", e)
        return jsonify({"error": "Could not fetch smart recommendations"}), 500
