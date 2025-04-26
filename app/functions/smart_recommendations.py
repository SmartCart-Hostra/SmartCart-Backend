# functions/smart_recommendations.py

def build_user_profile(saved_recipes):
    tag_counts = {}
    ingredient_counts = {}

    for recipe in saved_recipes:
        for tag in recipe.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        for ing in recipe.get("ingredients", []):
            ingredient_counts[ing] = ingredient_counts.get(ing, 0) + 1

    return {
        "tags": tag_counts,
        "ingredients": ingredient_counts
    }

def score_recipe(recipe, profile, preferences):
    score = 0
    ingredient_score = 0
    tag_score = 0
    preference_score = 0

    for tag in recipe.get("tags", []):
        tag_score += profile["tags"].get(tag, 0)

    for ing in recipe.get("ingredients", []):
        ingredient_score += profile["ingredients"].get(ing, 0)

    # Basic preference match scoring
    if preferences:
        if recipe.get("diet") == preferences.get("diet"):
            preference_score += 2
        if recipe.get("cuisine") == preferences.get("cuisine"):
            preference_score += 1
        if any(x in preferences.get("excludeIngredients", []) for x in recipe.get("ingredients", [])):
            preference_score -= 3  # penalize unwanted ingredients

    # Weighted sum (can adjust weights later)
    score = (ingredient_score * 0.5) + (tag_score * 0.3) + (preference_score * 0.2)

    return round(score, 2)
