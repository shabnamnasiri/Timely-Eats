from flask import request, jsonify, session

def register_review_routes(app, mysql):

    @app.route('/<int:item_id>/review', methods=["POST"])
    def submit_review(item_id):
        # check login
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({'error': 'User must be logged in'}), 401

        rating = request.form.get("rating")
        comment = request.form.get("comment", "").strip()

        # logical checks
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                return jsonify({'error': 'rating must be between 1 and 5'}), 400
        except (TypeError, ValueError):
            return jsonify({'error': 'rating must be a number'}), 400

        try:
            cursor = mysql.connection.cursor()
            sql = """
            INSERT INTO Review (user_id, item_id, rating, comment)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (user_id, item_id, rating, comment))
            mysql.connection.commit()
            cursor.close()
            return jsonify({'message': 'Review submitted successfully'}), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500


    @app.route('/item/<int:item_id>/avg-rating', methods=["GET"])
    def get_item_avg_rating(item_id):
        try:
            cursor = mysql.connection.cursor()
            sql = "SELECT AVG(rating) FROM Review WHERE item_id = %s"
            cursor.execute(sql, (item_id,))
            result = cursor.fetchone()
            avg_rating = result[0] if result[0] is not None else 0
            cursor.close()
            return jsonify({'item_id': item_id, 'avg_rating': round(float(avg_rating), 2)}), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500