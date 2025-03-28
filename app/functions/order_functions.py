from flask import jsonify, request
from bson.objectid import ObjectId
from app.models.cart_model import cart_items_collection, orders_collection
from app.functions.cart_functions import get_cart_items, clear_cart
import datetime
import re
import random
import string

def generate_order_number():
    """Generate a unique order number"""
    prefix = "ORD"
    timestamp = datetime.datetime.now().strftime("%Y%m%d")
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefix}-{timestamp}-{random_suffix}"

def validate_shipping_info(shipping_info):
    """Simple validation for shipping information"""
    return {}

def validate_payment_info(payment_info):
    """Simple validation for payment information"""
    return {}

def checkout(current_user):
    """Process checkout and create a new order"""
    data = request.json
    
    if not data:
        return jsonify({'message': 'Missing request data'}), 400
    
    # Get recipe items
    recipe_items = data.get('recipe_items', [])
    if not recipe_items:
        return jsonify({'message': 'No recipe items provided'}), 400
    
    # Process recipe items and calculate total price
    processed_items = []
    total_price = 0
    
    for recipe_item in recipe_items:
        recipe_id = recipe_item.get('recipe_id')
        if not recipe_id:
            continue
            
        # Process each ingredient in the recipe
        for ingredient in recipe_item.get('ingredients', []):
            kroger_item = ingredient.get('kroger_item', {})
            if not kroger_item:
                continue
                
            processed_item = {
                'recipe_id': recipe_id,
                'recipe_name': recipe_item.get('recipe_name', ''),
                'ingredient_name': ingredient.get('name', ''),
                'kroger_item': {
                    'product_id': kroger_item.get('productId'),
                    'name': kroger_item.get('description', ''),
                    'price': kroger_item.get('items', [{}])[0].get('price', {}).get('regular', 0),
                    'quantity': ingredient.get('quantity', 1)
                }
            }
            processed_items.append(processed_item)
            total_price += processed_item['kroger_item']['price'] * processed_item['kroger_item']['quantity']
    
    if not processed_items:
        return jsonify({'message': 'No valid items to process'}), 400
    
    # Create a new order with a unique order number
    order = {
        'order_number': generate_order_number(),
        'user_email': current_user['email'],
        'items': processed_items,
        'total_price': round(total_price, 2),
        'status': 'pending',
        'shipping_info': data.get('shipping_info', {}),
        'payment_info': data.get('payment_info', {}),
        'created_at': datetime.datetime.utcnow()
    }
    
    # Insert the order into the database
    result = orders_collection.insert_one(order)
    
    # Return the order details
    return jsonify({
        'message': 'Order placed successfully',
        'order_id': str(result.inserted_id),
        'order_number': order['order_number'],
        'total_price': order['total_price'],
        'status': order['status'],
        'created_at': order['created_at']
    }), 201

def get_order_history(current_user):
    """Get order history for the current user"""
    # Optional query parameters for filtering
    status = request.args.get('status')
    
    # Build query
    query = {'user_email': current_user['email']}
    if status:
        query['status'] = status
    
    # Execute query and sort by creation date (newest first)
    orders = orders_collection.find(query).sort('created_at', -1)
    
    # Convert MongoDB objects to JSON-serializable format
    result = []
    for order in orders:
        result.append({
            'id': str(order['_id']),
            'order_number': order['order_number'],
            'total_price': order['total_price'],
            'status': order['status'],
            'items_count': len(order['items']),
            'created_at': order['created_at']
        })
    
    return jsonify({
        'orders': result,
        'count': len(result)
    }), 200

def get_order_details(current_user, order_id):
    """Get detailed information for a specific order"""
    try:
        order_obj_id = ObjectId(order_id)
    except:
        return jsonify({'message': 'Invalid order_id format'}), 400
    
    order = orders_collection.find_one({
        '_id': order_obj_id,
        'user_email': current_user['email']
    })
    
    if not order:
        return jsonify({'message': 'Order not found'}), 404
    
    # Convert MongoDB object to JSON-serializable format
    result = {
        'id': str(order['_id']),
        'order_number': order['order_number'],
        'items': order['items'],
        'total_price': order['total_price'],
        'status': order['status'],
        'shipping_info': order['shipping_info'],
        'payment_info': order['payment_info'],
        'created_at': order['created_at']
    }
    
    return jsonify(result), 200

def cancel_order(current_user, order_id):
    """Cancel an order if it's in pending status"""
    try:
        order_obj_id = ObjectId(order_id)
    except:
        return jsonify({'message': 'Invalid order_id format'}), 400
    
    # Find the order first to check its status
    order = orders_collection.find_one({
        '_id': order_obj_id,
        'user_email': current_user['email']
    })
    
    if not order:
        return jsonify({'message': 'Order not found'}), 404
    
    # Check if order can be canceled (only pending orders)
    if order['status'] != 'pending':
        return jsonify({'message': f"Cannot cancel order in '{order['status']}' status"}), 400
    
    # Update order status to canceled
    result = orders_collection.update_one(
        {'_id': order_obj_id},
        {'$set': {'status': 'canceled'}}
    )
    
    return jsonify({'message': 'Order canceled successfully'}), 200