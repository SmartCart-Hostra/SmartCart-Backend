from flask import jsonify, request
from bson.objectid import ObjectId
from app import saved_recipes_collection
from app.functions.recipe_functions import fetch_recipe_detail
import datetime

def get_saved_recipes(current_user):
    """Get all saved recipes for the current user"""
    saved_recipes = saved_recipes_collection.find({'user_email': current_user['email']})
    
    # Convert MongoDB objects to JSON-serializable format
    result = []
    for recipe in saved_recipes:
        result.append({
            'id': str(recipe['_id']),
            'recipe_id': recipe['recipe_id'],
            'title': recipe.get('title', ''),
            'image': recipe.get('image', ''),
            'saved_at': recipe.get('saved_at')
        })
    
    return jsonify({
        'saved_recipes': result,
        'count': len(result)
    }), 200

def save_recipe(current_user):
    """Save a recipe for the current user"""
    data = request.json
    
    if not data or not data.get('recipe_id'):
        return jsonify({'message': 'Missing recipe_id field'}), 400
    
    recipe_id = data['recipe_id']
    
    # Check if recipe already saved
    existing = saved_recipes_collection.find_one({
        'user_email': current_user['email'],
        'recipe_id': recipe_id
    })
    
    if existing:
        return jsonify({'message': 'Recipe already saved'}), 409
    
    # Get recipe details to store name and image
    recipe_details, status_code = fetch_recipe_detail(recipe_id)
    
    if status_code != 200:
        return jsonify({'message': 'Failed to fetch recipe details'}), status_code
    
    # Create new saved recipe record
    new_saved_recipe = {
        'user_email': current_user['email'],
        'recipe_id': recipe_id,
        'title': recipe_details.get('title', ''),
        'image': recipe_details.get('image', ''),
        'saved_at': datetime.datetime.utcnow()
    }
    
    saved_recipes_collection.insert_one(new_saved_recipe)
    
    return jsonify({
        'message': 'Recipe saved successfully',
        'recipe': {
            'recipe_id': recipe_id,
            'title': recipe_details.get('title', ''),
            'image': recipe_details.get('image', '')
        }
    }), 201

def remove_saved_recipe(current_user):
    """Remove a saved recipe for the current user"""
    data = request.json
    
    if not data or not data.get('recipe_id'):
        return jsonify({'message': 'Missing recipe_id field'}), 400
    
    recipe_id = data['recipe_id']
    
    result = saved_recipes_collection.delete_one({
        'user_email': current_user['email'],
        'recipe_id': recipe_id
    })
    
    if result.deleted_count == 0:
        return jsonify({'message': 'Recipe not found or already removed'}), 404
    
    return jsonify({
        'message': 'Recipe removed successfully',
        'recipe_id': recipe_id
    }), 200