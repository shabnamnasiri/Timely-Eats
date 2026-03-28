from flask import Blueprint, request, jsonify
import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG  

#blueprint for run.py
add_item_bp = Blueprint('add_item', __name__)

@add_item_bp.route('/add-item', methods=["POST"])
def add_to_cart():
    # getting the input from html form
    cart_id = request.form.get("cart_id")
    item_id = request.form.get("item_id")
    quantity = request.form.get("quantity")
    customization_note = request.form.get("customization_note", "").strip()

    #to check if cart or item exists
    if not item_id or not cart_id:
        return jsonify({'error': 'cart_id and item_id are required'}), 400

    #to check the logic of qnt , not under 1
    try:
        quantity = int(quantity)
        if quantity < 1:
            return jsonify({'error': 'quantity must be at least 1'}), 400
    except (TypeError, ValueError):
        return jsonify({'error': 'quantity must be a positive integer'}), 400

    #db connection
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        sql = """
        INSERT INTO cart_items (cart_id, item_id, quantity, customization_note)
        VALUES (%s, %s, %s, %s)
        """

        #insertion to db
        cursor.execute(sql, (cart_id, item_id, quantity, customization_note))
        connection.commit()
        return jsonify({'message': 'Item added to cart successfully'}), 200
    
    #all other errors
    except Error as e:
        return jsonify({'error': str(e)}), 500
    
    #closing db connection
    finally:
        if cursor: cursor.close()
        if connection: connection.close()