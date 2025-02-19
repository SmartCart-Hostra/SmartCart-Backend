from flask import jsonify
from app import diet_preferences_collection
from app.functions.auth_functions import token_required

def get_diet_prefs(current_user):
    preferences = diet_preferences_collection.find_one({'email': current_user['email']})
    return jsonify({'preferences': preferences['preferences'] if preferences else []}), 200

def add_diet_pref(current_user):
    data = request.json
    if not data or not data.get('preference'):
        return jsonify({'message': 'Missing preference field'}), 400
    
    result = diet_preferences_collection.update_one(
        {'email': current_user['email']},
        {'$addToSet': {'preferences': data['preference'].lower()}},
        upsert=True
    )
    return jsonify({'message': 'Preference added successfully'}), 201

def remove_diet_pref(current_user):
    data = request.json
    if not data or not data.get('preference'):
        return jsonify({'message': 'Missing preference field'}), 400
    
    result = diet_preferences_collection.update_one(
        {'email': current_user['email']},
        {'$pull': {'preferences': data['preference'].lower()}}
    )
    
    if result.modified_count == 0:
        return jsonify({'message': 'Preference not found'}), 404
    return jsonify({'message': 'Preference removed successfully'}), 200