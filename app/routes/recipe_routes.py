from flask import Blueprint, request, jsonify
from app.functions.recipe_functions import recipes, recipe_ingredients
from app.functions.auth_functions import token_required 

recipe_routes = Blueprint('recipe_routes', __name__)

@recipe_routes.route("/recipes", methods=['GET'])
@token_required # add iddentification 
def recipes_route(current_user):
    return recipes()

@recipe_routes.route("/recipe/<int:recipe_id>", methods=['GET'])
@token_required # add iddentification 
def recipe_ingredients_route(current_user,recipe_id):
    return recipe_ingredients(recipe_id)