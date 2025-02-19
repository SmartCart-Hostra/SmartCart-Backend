from flask import Blueprint
from app.functions.auth_functions import token_required
from app.functions.preference_functions import (
    get_diets, add_diet, remove_diet,
    get_intolerances, add_intolerance, remove_intolerance,
    get_cuisines, add_cuisine, remove_cuisine
)

preference_routes = Blueprint('preference_routes', __name__)

# Diet Routes
@preference_routes.route('/diets', methods=['GET'])
@token_required
def get_diets_route(current_user):
    return get_diets(current_user)

@preference_routes.route('/diets', methods=['POST'])
@token_required
def add_diet_route(current_user):
    return add_diet(current_user)

@preference_routes.route('/diets', methods=['DELETE'])
@token_required
def remove_diet_route(current_user):
    return remove_diet(current_user)

# Intolerance Routes
@preference_routes.route('/intolerances', methods=['GET'])
@token_required
def get_intolerances_route(current_user):
    return get_intolerances(current_user)

@preference_routes.route('/intolerances', methods=['POST'])
@token_required
def add_intolerance_route(current_user):
    return add_intolerance(current_user)

@preference_routes.route('/intolerances', methods=['DELETE'])
@token_required
def remove_intolerance_route(current_user):
    return remove_intolerance(current_user)

# Cuisine Routes
@preference_routes.route('/cuisines', methods=['GET'])
@token_required
def get_cuisines_route(current_user):
    return get_cuisines(current_user)

@preference_routes.route('/cuisines', methods=['POST'])
@token_required
def add_cuisine_route(current_user):
    return add_cuisine(current_user)

@preference_routes.route('/cuisines', methods=['DELETE'])
@token_required
def remove_cuisine_route(current_user):
    return remove_cuisine(current_user)