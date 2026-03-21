from flask import Blueprint, request, jsonify, session
import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG  

#blueprint for run.py
review_bp = Blueprint('review', __name__)

@review_bp.route('/<int:item_id>/review', methods=["POST"])
def submit_review():

    #getting the input from html form
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({'error': 'User must be logged in'}), 401

    item_id = request.form.get("item_id")
    rating = request.form.get("rating")
    comment = request.form.get("comment", "").strip()

    #logical checks
    if not item_id:
        return jsonify({'error': 'item_id is required'}), 400

    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            return jsonify({'error': 'rating must be between 1 and 5'}), 400
    except (TypeError, ValueError):
        return jsonify({'error': 'rating must be a number'}), 400

    #connecting to db and insert
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        sql = """
        INSERT INTO review (user_id, item_id, rating, comment)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (user_id, item_id, rating, comment))
        connection.commit()
        return jsonify({'message': 'review submitted successfully'}), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if connection: connection.close()



@review_bp.route('/item/<int:item_id>/avg-rating', methods=["GET"])
def get_item_avg_rating(item_id):
    try:
        #connetion to db 
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        sql = "SELECT AVG(rating) FROM review WHERE item_id = %s"
        cursor.execute(sql, (item_id,))
        result = cursor.fetchone()
        avg_rating = result[0] if result[0] is not None else 0  # 0 if no reviews
        return jsonify({'item_id': item_id, 'avg_rating': round(avg_rating, 2)}), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if connection: connection.close()