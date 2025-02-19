from flask import jsonify, request
from app import diet_preferences_collection
from app.functions.auth_functions import token_required

ALLOWED_PREFERENCES = {
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

def validate_preference(input_pref):
    """Convert input to lowercase and match with allowed preferences"""
    lower_pref = input_pref.strip().lower()
    return ALLOWED_PREFERENCES.get(lower_pref)

def get_diet_prefs(current_user):
    preferences = diet_preferences_collection.find_one({'email': current_user['email']})
    return jsonify({'preferences': preferences['preferences'] if preferences else []}), 200

def add_diet_pref(current_user):
    data = request.json
    if not data or not data.get('preference'):
        return jsonify({'message': 'Missing preference field'}), 400
    
    pref = validate_preference(data['preference'])
    if not pref:
        return jsonify({
            'message': 'Invalid diet preference',
            'allowed': list(ALLOWED_PREFERENCES.values())
        }), 400
    
    result = diet_preferences_collection.update_one(
        {'email': current_user['email']},
        {'$addToSet': {'preferences': pref}},
        upsert=True
    )
    return jsonify({'message': 'Preference added successfully'}), 201

def remove_diet_pref(current_user):
    data = request.json
    if not data or not data.get('preference'):
        return jsonify({'message': 'Missing preference field'}), 400
    
    pref = validate_preference(data['preference'])
    if not pref:
        return jsonify({
            'message': 'Invalid diet preference',
            'allowed': list(ALLOWED_PREFERENCES.values())
        }), 400
    
    result = diet_preferences_collection.update_one(
        {'email': current_user['email']},
        {'$pull': {'preferences': pref}}
    )
    
    if result.modified_count == 0:
        return jsonify({'message': 'Preference not found'}), 404
    return jsonify({'message': 'Preference removed successfully'}), 200