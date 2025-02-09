from flask import Blueprint, request, jsonify
from app.functions.recipe_functions import recipes, recipe_ingredients

recipe_routes = Blueprint('recipe_routes', __name__)

@recipe_routes.route("/recipes", methods=['GET'])
def recipes_route():
    return recipes()

@recipe_routes.route("/recipe/<int:recipe_id>", methods=['GET'])
def recipe_ingredients_route(recipe_id):
    return recipe_ingredients(recipe_id)