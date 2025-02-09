from flask import Blueprint, request, jsonify, make_response
from app.functions.auth_functions import signup, login, verify_2fa, login_verify, logout, protected_route

auth_routes = Blueprint('auth_routes', __name__)

@auth_routes.route('/signup', methods=['POST'])
def signup_route():
    return signup()

@auth_routes.route('/verify-2fa', methods=['POST'])
def verify_2fa_route():
    return verify_2fa()

@auth_routes.route('/login', methods=['POST'])
def login_route():
    return login()

@auth_routes.route('/login-verify', methods=['POST'])
def login_verify_route():
    return login_verify()

@auth_routes.route('/logout', methods=['POST'])
def logout_route():
    return logout()

@auth_routes.route('/protected', methods=['GET'])
def protected_route_route():
    return protected_route()