from flask import Blueprint, request, jsonify
from app.functions.kroger_functions import get_access_token, search_products, kroger_search, kroger_recipe_ingredients_info

kroger_routes = Blueprint('kroger_routes', __name__)

@kroger_routes.route("/kroger")
def kroger_search_route():
    return kroger_search()

@kroger_routes.route("/kroger/recipe/<int:recipe_id>")
def kroger_recipe_ingredients_info_route(recipe_id):
    return kroger_recipe_ingredients_info(recipe_id)