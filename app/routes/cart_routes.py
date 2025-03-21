from flask import Blueprint
from app.functions.auth_functions import token_required
from app.functions.cart_functions import (
    get_cart_items, add_to_cart, update_cart_item,
    remove_from_cart, clear_cart
)

cart_routes = Blueprint('cart_routes', __name__)

@cart_routes.route('/cart', methods=['GET'])
@token_required
def get_cart_route(current_user):
    return get_cart_items(current_user)

@cart_routes.route('/cart', methods=['POST'])
@token_required
def add_to_cart_route(current_user):
    return add_to_cart(current_user)

@cart_routes.route('/cart', methods=['PUT'])
@token_required
def update_cart_item_route(current_user):
    return update_cart_item(current_user)

@cart_routes.route('/cart', methods=['DELETE'])
@token_required
def remove_from_cart_route(current_user):
    return remove_from_cart(current_user)

@cart_routes.route('/cart/clear', methods=['POST'])
@token_required
def clear_cart_route(current_user):
    return clear_cart(current_user)