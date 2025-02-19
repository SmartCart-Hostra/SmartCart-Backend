from flask import jsonify, request
from app import user_preferences_collection
from app.functions.auth_functions import token_required

# Diet Preferences
ALLOWED_DIETS = {
    'gluten free': 'Gluten Free',
    'ketogenic': 'Ketogenic',
    'vegetarian': 'Vegetarian',
    'lacto-vegetarian': 'Lacto-Vegetarian',
    'ovo-vegetarian': 'Ovo-Vegetarian',
    'vegan': 'Vegan',
    'pescetarian': 'Pescetarian',
    'paleo': 'Paleo',
    'primal': 'Primal',
    'low fodmap': 'Low FODMAP',
    'whole30': 'Whole30'
}

# Intolerances
ALLOWED_INTOLERANCES = {
    'dairy', 'egg', 'gluten', 'peanut', 'sesame',
    'seafood', 'shellfish', 'soy', 'tree nut', 'wheat'
}

# Cuisines
ALLOWED_CUISINES = {
    "African", "American", "British", "Cajun", "Caribbean",
    "Chinese", "Eastern European", "French", "German", "Greek",
    "Indian", "Irish", "Italian", "Japanese", "Jewish", "Korean",
    "Latin American", "Mediterranean", "Mexican", "Middle Eastern",
    "Nordic", "Southern", "Spanish", "Thai", "Vietnamese"
}

def validate_diet(input_diet):
    lower_diet = input_diet.strip().lower()
    return ALLOWED_DIETS.get(lower_diet)

def validate_intolerance(input_intolerance):
    lower_intol = input_intolerance.strip().lower()
    return lower_intol if lower_intol in ALLOWED_INTOLERANCES else None

def validate_cuisine(input_cuisine):
    title_cuisine = input_cuisine.strip().title()
    return title_cuisine if title_cuisine in ALLOWED_CUISINES else None

# Diet Endpoints
def get_diets(current_user):
    prefs = user_preferences_collection.find_one({'email': current_user['email']})
    return jsonify({'diets': prefs.get('diets', []) if prefs else []}), 200

def add_diet(current_user):
    data = request.json
    if not data or not data.get('diet'):
        return jsonify({'message': 'Missing diet field'}), 400
    
    diet = validate_diet(data['diet'])
    if not diet:
        return jsonify({
            'message': 'Invalid diet',
            'allowed': list(ALLOWED_DIETS.values())
        }), 400
    
    user_preferences_collection.update_one(
        {'email': current_user['email']},
        {'$addToSet': {'diets': diet}},
        upsert=True
    )
    return jsonify({'message': 'Diet added successfully'}), 201

def remove_diet(current_user):
    data = request.json
    if not data or not data.get('diet'):
        return jsonify({'message': 'Missing diet field'}), 400
    
    diet = validate_diet(data['diet'])
    if not diet:
        return jsonify({
            'message': 'Invalid diet',
            'allowed': list(ALLOWED_DIETS.values())
        }), 400
    
    result = user_preferences_collection.update_one(
        {'email': current_user['email']},
        {'$pull': {'diets': diet}}
    )
    if result.modified_count == 0:
        return jsonify({'message': 'Diet not found'}), 404
    return jsonify({'message': 'Diet removed successfully'}), 200

# Intolerance Endpoints
def get_intolerances(current_user):
    prefs = user_preferences_collection.find_one({'email': current_user['email']})
    return jsonify({'intolerances': prefs.get('intolerances', []) if prefs else []}), 200

def add_intolerance(current_user):
    data = request.json
    if not data or not data.get('intolerance'):
        return jsonify({'message': 'Missing intolerance field'}), 400
    
    intolerance = validate_intolerance(data['intolerance'])
    if not intolerance:
        return jsonify({
            'message': 'Invalid intolerance',
            'allowed': list(ALLOWED_INTOLERANCES)
        }), 400
    
    user_preferences_collection.update_one(
        {'email': current_user['email']},
        {'$addToSet': {'intolerances': intolerance}},
        upsert=True
    )
    return jsonify({'message': 'Intolerance added successfully'}), 201

def remove_intolerance(current_user):
    data = request.json
    if not data or not data.get('intolerance'):
        return jsonify({'message': 'Missing intolerance field'}), 400
    
    intolerance = validate_intolerance(data['intolerance'])
    if not intolerance:
        return jsonify({
            'message': 'Invalid intolerance',
            'allowed': list(ALLOWED_INTOLERANCES)
        }), 400
    
    result = user_preferences_collection.update_one(
        {'email': current_user['email']},
        {'$pull': {'intolerances': intolerance}}
    )
    if result.modified_count == 0:
        return jsonify({'message': 'Intolerance not found'}), 404
    return jsonify({'message': 'Intolerance removed successfully'}), 200

# Cuisine Endpoints
def get_cuisines(current_user):
    prefs = user_preferences_collection.find_one({'email': current_user['email']})
    return jsonify({'cuisines': prefs.get('cuisines', []) if prefs else []}), 200

def add_cuisine(current_user):
    data = request.json
    if not data or not data.get('cuisine'):
        return jsonify({'message': 'Missing cuisine field'}), 400
    
    cuisine = validate_cuisine(data['cuisine'])
    if not cuisine:
        return jsonify({
            'message': 'Invalid cuisine',
            'allowed': sorted(ALLOWED_CUISINES)
        }), 400
    
    user_preferences_collection.update_one(
        {'email': current_user['email']},
        {'$addToSet': {'cuisines': cuisine}},
        upsert=True
    )
    return jsonify({'message': 'Cuisine added successfully'}), 201

def remove_cuisine(current_user):
    data = request.json
    if not data or not data.get('cuisine'):
        return jsonify({'message': 'Missing cuisine field'}), 400
    
    cuisine = validate_cuisine(data['cuisine'])
    if not cuisine:
        return jsonify({
            'message': 'Invalid cuisine',
            'allowed': sorted(ALLOWED_CUISINES)
        }), 400
    
    result = user_preferences_collection.update_one(
        {'email': current_user['email']},
        {'$pull': {'cuisines': cuisine}}
    )
    if result.modified_count == 0:
        return jsonify({'message': 'Cuisine not found'}), 404
    return jsonify({'message': 'Cuisine removed successfully'}), 200