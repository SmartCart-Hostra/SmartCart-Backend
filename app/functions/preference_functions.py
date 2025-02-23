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

def add_diets(current_user):
    data = request.json
    if not data or not data.get('diets') or not isinstance(data['diets'], list):
        return jsonify({'message': 'Missing diets field or invalid format. Expected array of diets'}), 400
    
    # Validate all diets first
    validated_diets = []
    invalid_diets = []
    for diet in data['diets']:
        validated = validate_diet(diet)
        if validated:
            validated_diets.append(validated)
        else:
            invalid_diets.append(diet)
    
    if invalid_diets:
        return jsonify({
            'message': 'Invalid diets found',
            'invalid_diets': invalid_diets,
            'allowed': list(ALLOWED_DIETS.values())
        }), 400
    
    if not validated_diets:
        return jsonify({'message': 'No valid diets to add'}), 400
    
    # Add all valid diets at once
    user_preferences_collection.update_one(
        {'email': current_user['email']},
        {'$addToSet': {'diets': {'$each': validated_diets}}},
        upsert=True
    )
    
    return jsonify({
        'message': 'Diets added successfully',
        'added_diets': validated_diets
    }), 201

def remove_diets(current_user):
    data = request.json
    if not data or not data.get('diets') or not isinstance(data['diets'], list):
        return jsonify({'message': 'Missing diets field or invalid format. Expected array of diets'}), 400
    
    # Validate all diets first
    validated_diets = []
    invalid_diets = []
    for diet in data['diets']:
        validated = validate_diet(diet)
        if validated:
            validated_diets.append(validated)
        else:
            invalid_diets.append(diet)
    
    if invalid_diets:
        return jsonify({
            'message': 'Invalid diets found',
            'invalid_diets': invalid_diets,
            'allowed': list(ALLOWED_DIETS.values())
        }), 400
    
    if not validated_diets:
        return jsonify({'message': 'No valid diets to remove'}), 400
    
    # Remove all valid diets at once
    result = user_preferences_collection.update_one(
        {'email': current_user['email']},
        {'$pull': {'diets': {'$in': validated_diets}}}
    )
    
    if result.modified_count == 0:
        return jsonify({'message': 'No diets were found to remove'}), 404
    
    return jsonify({
        'message': 'Diets removed successfully',
        'removed_diets': validated_diets
    }), 200

# Intolerance Endpoints
def get_intolerances(current_user):
    prefs = user_preferences_collection.find_one({'email': current_user['email']})
    return jsonify({'intolerances': prefs.get('intolerances', []) if prefs else []}), 200

def add_intolerances(current_user):
    data = request.json
    if not data or not data.get('intolerances') or not isinstance(data['intolerances'], list):
        return jsonify({'message': 'Missing intolerances field or invalid format. Expected array of intolerances'}), 400
    
    validated_intolerances = []
    invalid_intolerances = []
    for intolerance in data['intolerances']:
        validated = validate_intolerance(intolerance)
        if validated:
            validated_intolerances.append(validated)
        else:
            invalid_intolerances.append(intolerance)
    
    if invalid_intolerances:
        return jsonify({
            'message': 'Invalid intolerances found',
            'invalid_intolerances': invalid_intolerances,
            'allowed': list(ALLOWED_INTOLERANCES)
        }), 400
    
    if not validated_intolerances:
        return jsonify({'message': 'No valid intolerances to add'}), 400
    
    user_preferences_collection.update_one(
        {'email': current_user['email']},
        {'$addToSet': {'intolerances': {'$each': validated_intolerances}}},
        upsert=True
    )
    
    return jsonify({
        'message': 'Intolerances added successfully',
        'added_intolerances': validated_intolerances
    }), 201

def remove_intolerances(current_user):
    data = request.json
    if not data or not data.get('intolerances') or not isinstance(data['intolerances'], list):
        return jsonify({'message': 'Missing intolerances field or invalid format. Expected array of intolerances'}), 400
    
    validated_intolerances = []
    invalid_intolerances = []
    for intolerance in data['intolerances']:
        validated = validate_intolerance(intolerance)
        if validated:
            validated_intolerances.append(validated)
        else:
            invalid_intolerances.append(intolerance)
    
    if invalid_intolerances:
        return jsonify({
            'message': 'Invalid intolerances found',
            'invalid_intolerances': invalid_intolerances,
            'allowed': list(ALLOWED_INTOLERANCES)
        }), 400
    
    if not validated_intolerances:
        return jsonify({'message': 'No valid intolerances to remove'}), 400
    
    result = user_preferences_collection.update_one(
        {'email': current_user['email']},
        {'$pull': {'intolerances': {'$in': validated_intolerances}}}
    )
    
    if result.modified_count == 0:
        return jsonify({'message': 'No intolerances were found to remove'}), 404
    
    return jsonify({
        'message': 'Intolerances removed successfully',
        'removed_intolerances': validated_intolerances
    }), 200

# Cuisine Endpoints
def get_cuisines(current_user):
    prefs = user_preferences_collection.find_one({'email': current_user['email']})
    return jsonify({'cuisines': prefs.get('cuisines', []) if prefs else []}), 200

def add_cuisines(current_user):
    data = request.json
    if not data or not data.get('cuisines') or not isinstance(data['cuisines'], list):
        return jsonify({'message': 'Missing cuisines field or invalid format. Expected array of cuisines'}), 400
    
    validated_cuisines = []
    invalid_cuisines = []
    for cuisine in data['cuisines']:
        validated = validate_cuisine(cuisine)
        if validated:
            validated_cuisines.append(validated)
        else:
            invalid_cuisines.append(cuisine)
    
    if invalid_cuisines:
        return jsonify({
            'message': 'Invalid cuisines found',
            'invalid_cuisines': invalid_cuisines,
            'allowed': sorted(ALLOWED_CUISINES)
        }), 400
    
    if not validated_cuisines:
        return jsonify({'message': 'No valid cuisines to add'}), 400
    
    user_preferences_collection.update_one(
        {'email': current_user['email']},
        {'$addToSet': {'cuisines': {'$each': validated_cuisines}}},
        upsert=True
    )
    
    return jsonify({
        'message': 'Cuisines added successfully',
        'added_cuisines': validated_cuisines
    }), 201

def remove_cuisines(current_user):
    data = request.json
    if not data or not data.get('cuisines') or not isinstance(data['cuisines'], list):
        return jsonify({'message': 'Missing cuisines field or invalid format. Expected array of cuisines'}), 400
    
    validated_cuisines = []
    invalid_cuisines = []
    for cuisine in data['cuisines']:
        validated = validate_cuisine(cuisine)
        if validated:
            validated_cuisines.append(validated)
        else:
            invalid_cuisines.append(cuisine)
    
    if invalid_cuisines:
        return jsonify({
            'message': 'Invalid cuisines found',
            'invalid_cuisines': invalid_cuisines,
            'allowed': sorted(ALLOWED_CUISINES)
        }), 400
    
    if not validated_cuisines:
        return jsonify({'message': 'No valid cuisines to remove'}), 400
    
    result = user_preferences_collection.update_one(
        {'email': current_user['email']},
        {'$pull': {'cuisines': {'$in': validated_cuisines}}}
    )
    
    if result.modified_count == 0:
        return jsonify({'message': 'No cuisines were found to remove'}), 404
    
    return jsonify({
        'message': 'Cuisines removed successfully',
        'removed_cuisines': validated_cuisines
    }), 200