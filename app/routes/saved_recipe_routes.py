from flask import Blueprint, jsonify, request
from app.functions.auth_functions import token_required
from app.functions.saved_recipe_functions import (
    get_saved_recipes, save_recipe, remove_saved_recipe
)

saved_recipe_routes = Blueprint('saved_recipe_routes', __name__)

@saved_recipe_routes.route('/saved-recipes', methods=['GET'])
@token_required
def get_saved_recipes_route(current_user):
    return get_saved_recipes(current_user)

@saved_recipe_routes.route('/saved-recipes', methods=['POST'])
@token_required
def save_recipe_route(current_user):
    return save_recipe(current_user)

@saved_recipe_routes.route('/saved-recipes', methods=['DELETE'])
@token_required
def remove_saved_recipe_route(current_user):
    return remove_saved_recipe(current_user)