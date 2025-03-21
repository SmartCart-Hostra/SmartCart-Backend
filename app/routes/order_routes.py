from flask import Blueprint
from app.functions.auth_functions import token_required
from app.functions.order_functions import (
    checkout, get_order_history, get_order_details, cancel_order
)

order_routes = Blueprint('order_routes', __name__)

@order_routes.route('/checkout', methods=['POST'])
@token_required
def checkout_route(current_user):
    return checkout(current_user)

@order_routes.route('/orders', methods=['GET'])
@token_required
def get_order_history_route(current_user):
    return get_order_history(current_user)

@order_routes.route('/orders/<order_id>', methods=['GET'])
@token_required
def get_order_details_route(current_user, order_id):
    return get_order_details(current_user, order_id)

@order_routes.route('/orders/<order_id>/cancel', methods=['POST'])
@token_required
def cancel_order_route(current_user, order_id):
    return cancel_order(current_user, order_id)