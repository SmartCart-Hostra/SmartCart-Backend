import os
import requests
from flask import jsonify, request
from app import user_preferences_collection

API_KEY = os.getenv("API_KEY")

def get_recipes(current_user):
    try:
        query = request.args.get("query")
        prefs = user_preferences_collection.find_one(
            {"email": current_user["email"]}
        ) or {}

        params = {
            "query": query,
            "apiKey": API_KEY,
            "number": 10
        }

        # Add diets
        if prefs.get('diets'):
            params["diet"] = ",".join([d.lower() for d in prefs['diets']])

        # Add intolerances
        if prefs.get('intolerances'):
            params["intolerances"] = ",".join(prefs['intolerances'])

        # Add cuisines
        if prefs.get('cuisines'):
            params["cuisine"] = ",".join(prefs['cuisines'])

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
                    "cuisines": prefs.get('cuisines', [])
                }
            }
        }), 200

    except requests.exceptions.HTTPError as e:
        return jsonify({"error": f"Spoonacular API error: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500