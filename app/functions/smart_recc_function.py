# 📄 smart_recc_function.py

import openai
import numpy as np
from flask import jsonify
from app import saved_recipes_collection, user_preferences_collection
import requests
import os

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

SPOONACULAR_API_KEY = os.environ.get("API_KEY")

# -------------------- Embedding Helper -------------------- #
def get_embedding(text):
    response = openai.Embedding.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response['data'][0]['embedding']

# -------------------- Cosine Similarity -------------------- #
def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# -------------------- Recipe Fetching with Filters -------------------- #
def fetch_candidate_recipes(diets=None, intolerances=None):
    base_url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {
        "number": 15,
        "apiKey": SPOONACULAR_API_KEY,
        "addRecipeInformation": True
    }

    if diets:
        params["diet"] = ",".join(diets)
    if intolerances:
        params["intolerances"] = ",".join(intolerances)

    res = requests.get(base_url, params=params)
    if res.status_code != 200:
        print("❌ Spoonacular error:", res.text)
        return []

    data = res.json()
    return data.get("results", [])

# -------------------- Smart Recommendation Generator -------------------- #
def generate_smart_recommendations(current_user):
    user_email = current_user['email']
    saved = list(saved_recipes_collection.find({"user_email": user_email}))

    if len(saved) < 3:
        return jsonify({
            "showSmartRecommendations": False,
            "message": "Save at least 3 recipes to get personalized results."
        }), 200

    # Retrieve user diet/intolerance preferences
    user_prefs = user_preferences_collection.find_one({"email": user_email}) or {}
    diet_list = user_prefs.get("diets", [])
    intolerance_list = user_prefs.get("intolerances", [])

    # Embed saved recipes
    saved_titles = [r.get("title", "") for r in saved]
    saved_embeddings = [get_embedding(title) for title in saved_titles]
    user_profile = np.mean(saved_embeddings, axis=0)

    # Fetch filtered candidate recipes
    candidates = fetch_candidate_recipes(diet_list, intolerance_list)
    recommendations = []

    for recipe in candidates:
        title = recipe.get("title", "")
        image = recipe.get("image", "")
        id = recipe.get("id")

        try:
            emb = get_embedding(title)
            similarity = cosine_similarity(user_profile, emb)
            recommendations.append({
                "id": id,
                "title": title,
                "image": image,
                "match_score": round(similarity * 100, 2)
            })
        except Exception as e:
            continue

    # Sort and return top results
    top_results = sorted(recommendations, key=lambda x: x['match_score'], reverse=True)[:5]

    return jsonify({
        "showSmartRecommendations": True,
        "smartRecommendations": top_results
    }), 200
