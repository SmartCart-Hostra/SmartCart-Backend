from flask import Blueprint
from app.functions.auth_functions import token_required
from app.functions.preference_functions import get_diet_prefs, add_diet_pref, remove_diet_pref

preference_routes = Blueprint('preference_routes', __name__)

@preference_routes.route('/diet/preferences', methods=['GET'])
@token_required
def get_preferences_route(current_user):
    return get_diet_prefs(current_user)

@preference_routes.route('/diet/preferences', methods=['POST'])
@token_required
def add_preference_route(current_user):
    return add_diet_pref(current_user)

@preference_routes.route('/diet/preferences', methods=['DELETE'])
@token_required
def remove_preference_route(current_user):
    return remove_diet_pref(current_user)