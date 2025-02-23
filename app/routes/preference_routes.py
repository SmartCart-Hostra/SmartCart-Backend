from flask import Blueprint
from app.functions.auth_functions import token_required
from app.functions.preference_functions import (
    add_nutrition_goals, get_diets, add_diets, get_nutrition_goals, remove_diets,
    get_intolerances, add_intolerances, remove_intolerances,
    get_cuisines, add_cuisines, remove_cuisines, remove_nutrition_goals
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
    return add_diets(current_user)

@preference_routes.route('/diets', methods=['DELETE'])
@token_required
def remove_diet_route(current_user):
    return remove_diets(current_user)

# Intolerance Routes
@preference_routes.route('/intolerances', methods=['GET'])
@token_required
def get_intolerances_route(current_user):
    return get_intolerances(current_user)

@preference_routes.route('/intolerances', methods=['POST'])
@token_required
def add_intolerance_route(current_user):
    return add_intolerances(current_user)

@preference_routes.route('/intolerances', methods=['DELETE'])
@token_required
def remove_intolerance_route(current_user):
    return remove_intolerances(current_user)

# Cuisine Routes
@preference_routes.route('/cuisines', methods=['GET'])
@token_required
def get_cuisines_route(current_user):
    return get_cuisines(current_user)

@preference_routes.route('/cuisines', methods=['POST'])
@token_required
def add_cuisine_route(current_user):
    return add_cuisines(current_user)

@preference_routes.route('/cuisines', methods=['DELETE'])
@token_required
def remove_cuisine_route(current_user):
    return remove_cuisines(current_user)

# Nutrition Goal Routes
@preference_routes.route('/nutrition_goals', methods=['GET'])
@token_required
def get_nutrition_goals_route(current_user):
    return get_nutrition_goals(current_user)

@preference_routes.route('/nutrition_goals', methods=['POST'])
@token_required
def add_nutrition_goals_route(current_user):
    return add_nutrition_goals(current_user)

@preference_routes.route('/nutrition_goals', methods=['DELETE'])
@token_required
def remove_nutrition_goals_route(current_user):
    return remove_nutrition_goals(current_user)