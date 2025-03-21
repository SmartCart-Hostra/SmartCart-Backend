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
    """Validate shipping information"""
    errors = {}
    
    # Name validation
    if not shipping_info.get('full_name'):
        errors['full_name'] = 'Full name is required'
    
    # Email validation
    email = shipping_info.get('email', '')
    if not email:
        errors['email'] = 'Email is required'
    elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        errors['email'] = 'Invalid email format'
    
    # Phone validation
    phone = shipping_info.get('phone', '')
    if not phone:
        errors['phone'] = 'Phone number is required'
    elif not re.match(r"^\+?[\d\s\-\(\)]{10,15}$", phone):
        errors['phone'] = 'Invalid phone number format'
    
    # Address validation
    if not shipping_info.get('address_line1'):
        errors['address_line1'] = 'Address line 1 is required'
    
    if not shipping_info.get('city'):
        errors['city'] = 'City is required'
    
    if not shipping_info.get('state'):
        errors['state'] = 'State is required'
    
    if not shipping_info.get('postal_code'):
        errors['postal_code'] = 'Postal code is required'
    elif not re.match(r"^\d{5}(-\d{4})?$", shipping_info.get('postal_code', '')):
        errors['postal_code'] = 'Invalid US postal code format'
    
    return errors

def validate_payment_info(payment_info):
    """Validate payment information"""
    errors = {}
    
    # Card number validation
    card_number = payment_info.get('card_number', '')
    if not card_number:
        errors['card_number'] = 'Card number is required'
    elif not re.match(r"^\d{13,19}$", card_number.replace(' ', '')):
        errors['card_number'] = 'Invalid card number format'
    
    # Expiry date validation
    expiry = payment_info.get('expiry_date', '')
    if not expiry:
        errors['expiry_date'] = 'Expiry date is required'
    elif not re.match(r"^(0[1-9]|1[0-2])\/\d{2}$", expiry):
        errors['expiry_date'] = 'Invalid expiry date format (MM/YY)'
    else:
        month, year = expiry.split('/')
        current_year = datetime.datetime.now().year % 100
        current_month = datetime.datetime.now().month
        
        if (int(year) < current_year) or (int(year) == current_year and int(month) < current_month):
            errors['expiry_date'] = 'Card has expired'
    
    # CVV validation
    cvv = payment_info.get('cvv', '')
    if not cvv:
        errors['cvv'] = 'CVV is required'
    elif not re.match(r"^\d{3,4}$", cvv):
        errors['cvv'] = 'Invalid CVV format'
    
    # Cardholder name validation
    if not payment_info.get('cardholder_name'):
        errors['cardholder_name'] = 'Cardholder name is required'
    
    return errors

def checkout(current_user):
    """Process checkout and create a new order"""
    data = request.json
    
    if not data:
        return jsonify({'message': 'Missing request data'}), 400
    
    # Get cart items first
    cart_response, status_code = get_cart_items(current_user)
    if status_code != 200:
        return cart_response, status_code
    
    cart_data = cart_response.get_json()
    cart_items = cart_data.get('cart_items', [])
    
    if not cart_items:
        return jsonify({'message': 'Cannot checkout with empty cart'}), 400
    
    # Validate shipping information
    shipping_info = data.get('shipping_info', {})
    shipping_errors = validate_shipping_info(shipping_info)
    
    # Validate payment information
    payment_info = data.get('payment_info', {})
    payment_errors = validate_payment_info(payment_info)
    
    # If there are validation errors, return them
    if shipping_errors or payment_errors:
        return jsonify({
            'message': 'Validation failed',
            'errors': {
                'shipping': shipping_errors,
                'payment': payment_errors
            }
        }), 400
    
    # Create a new order with a unique order number
    order = {
        'order_number': generate_order_number(),
        'user_email': current_user['email'],
        'items': cart_items,
        'total_price': cart_data.get('total_price', 0),
        'status': 'pending',
        'shipping_info': {
            'full_name': shipping_info.get('full_name'),
            'email': shipping_info.get('email'),
            'phone': shipping_info.get('phone'),
            'address_line1': shipping_info.get('address_line1'),
            'address_line2': shipping_info.get('address_line2', ''),
            'city': shipping_info.get('city'),
            'state': shipping_info.get('state'),
            'postal_code': shipping_info.get('postal_code'),
            'country': shipping_info.get('country', 'United States')
        },
        'payment_info': {
            'cardholder_name': payment_info.get('cardholder_name'),
            # Store last 4 digits only for security
            'card_last4': payment_info.get('card_number', '')[-4:],
            'expiry_date': payment_info.get('expiry_date')
        },
        'created_at': datetime.datetime.utcnow()
    }
    
    # Insert the order into the database
    result = orders_collection.insert_one(order)
    
    # Clear the cart after successful checkout
    clear_cart(current_user)
    
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