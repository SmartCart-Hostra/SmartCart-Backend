from flask import Blueprint, request, jsonify
from app.functions.kroger_functions import get_access_token, search_products, kroger_search, kroger_recipe_ingredients_info, get_product_details
from app.functions.auth_functions import token_required 

kroger_routes = Blueprint('kroger_routes', __name__)

@kroger_routes.route("/krogerSearchItem", methods=['GET'])
@token_required # add iddentification 
def kroger_search_route(current_user):
#def kroger_search_route():
    return kroger_search()

@kroger_routes.route("/kroger/recipe/<int:recipe_id>", methods = ['GET'])
@token_required # add iddentification 
def kroger_recipe_ingredients_info_route(current_user,recipe_id):
#def kroger_recipe_ingredients_info_route(recipe_id):
    return kroger_recipe_ingredients_info(recipe_id)

@kroger_routes.route("/kroger/product/<string:product_id>", methods=['GET'])
@token_required
def get_product_details_route(current_user, product_id):
    """
    Returns detailed information about a specific Kroger product.
    """
    product_data, status_code = get_product_details(product_id)
    return jsonify(product_data), status_code