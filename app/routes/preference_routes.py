from flask import Blueprint
from app.functions.preference_functions import get_diet_prefs, add_diet_pref, remove_diet_pref

preference_routes = Blueprint('preference_routes', __name__)

@preference_routes.route('/diet/preferences', methods=['GET'])
def get_preferences_route():
    return get_diet_prefs(current_user)

@preference_routes.route('/diet/preferences', methods=['POST'])
def add_preference_route():
    return add_diet_pref(current_user)

@preference_routes.route('/diet/preferences', methods=['DELETE'])
def remove_preference_route():
    return remove_diet_pref(current_user)