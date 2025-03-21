from flask import jsonify, request
from bson.objectid import ObjectId
from app.models.cart_model import cart_items_collection
from app.functions.kroger_functions import get_access_token, get_kroger_product_details
import datetime

def get_cart_items(current_user):
    """Get all items in the user's shopping cart"""
    cart_items = cart_items_collection.find({'user_email': current_user['email']})
    
    # Convert MongoDB objects to JSON-serializable format
    result = []
    for item in cart_items:
        result.append({
            'id': str(item['_id']),
            'product_id': item['product_id'],
            'name': item.get('name', ''),
            'image': item.get('image', ''),
            'price': item.get('price', 0),
            'quantity': item.get('quantity', 1),
            'added_at': item.get('added_at')
        })
    
    # Calculate total price
    total_price = sum(item['price'] * item['quantity'] for item in result)
    
    return jsonify({
        'cart_items': result,
        'count': len(result),
        'total_price': round(total_price, 2)
    }), 200

def add_to_cart(current_user):
    """Add an item to the user's shopping cart"""
    data = request.json
    
    if not data or not data.get('product_id') or not data.get('name'):
        return jsonify({'message': 'Missing required fields (product_id, name)'}), 400
    
    product_id = data['product_id']
    
    # Check if item already in cart
    existing = cart_items_collection.find_one({
        'user_email': current_user['email'],
        'product_id': product_id
    })
    
    if existing:
        # Update quantity instead of adding new item
        new_quantity = existing['quantity'] + (data.get('quantity', 1))
        cart_items_collection.update_one(
            {'_id': existing['_id']},
            {'$set': {'quantity': new_quantity}}
        )
        return jsonify({'message': 'Item quantity updated in cart', 'item_id': str(existing['_id'])}), 200
    
    # Create new cart item
    new_cart_item = {
        'user_email': current_user['email'],
        'product_id': product_id,
        'name': data['name'],
        'image': data.get('image', ''),
        'price': data.get('price', 0),
        'quantity': data.get('quantity', 1),
        'added_at': datetime.datetime.utcnow()
    }
    
    result = cart_items_collection.insert_one(new_cart_item)
    
    return jsonify({
        'message': 'Item added to cart successfully',
        'item_id': str(result.inserted_id)
    }), 201

def update_cart_item(current_user):
    """Update quantity of an item in cart"""
    data = request.json
    
    if not data or not data.get('item_id') or 'quantity' not in data:
        return jsonify({'message': 'Missing required fields (item_id, quantity)'}), 400
    
    try:
        item_id = ObjectId(data['item_id'])
    except:
        return jsonify({'message': 'Invalid item_id format'}), 400
    
    quantity = data['quantity']
    
    if quantity <= 0:
        # If quantity is 0 or negative, remove the item
        return remove_from_cart(current_user)
    
    # Update item quantity
    result = cart_items_collection.update_one(
        {'_id': item_id, 'user_email': current_user['email']},
        {'$set': {'quantity': quantity}}
    )
    
    if result.matched_count == 0:
        return jsonify({'message': 'Item not found in cart'}), 404
    
    return jsonify({'message': 'Cart item updated successfully'}), 200

def remove_from_cart(current_user):
    """Remove an item from the shopping cart"""
    data = request.json
    
    if not data or not data.get('item_id'):
        return jsonify({'message': 'Missing item_id field'}), 400
    
    try:
        item_id = ObjectId(data['item_id'])
    except:
        return jsonify({'message': 'Invalid item_id format'}), 400
    
    result = cart_items_collection.delete_one({
        '_id': item_id,
        'user_email': current_user['email']
    })
    
    if result.deleted_count == 0:
        return jsonify({'message': 'Item not found in cart or already removed'}), 404
    
    return jsonify({'message': 'Item removed from cart successfully'}), 200

def clear_cart(current_user):
    """Remove all items from the user's shopping cart"""
    result = cart_items_collection.delete_many({
        'user_email': current_user['email']
    })
    
    return jsonify({
        'message': 'Cart cleared successfully',
        'items_removed': result.deleted_count
    }), 200