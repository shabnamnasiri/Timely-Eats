from flask import Blueprint, request, jsonify

add_item_bp = Blueprint('add_item', __name__)

def register_add_item_routes(app, mysql):
    @app.route('/add-item', methods=["POST"])
    def add_to_cart():
        cart_id = request.form.get("cart_id")
        item_id = request.form.get("item_id")
        quantity = request.form.get("quantity")
        customization_note = request.form.get("customization_note", "").strip()

        if not item_id or not cart_id:
            return jsonify({'error': 'cart_id and item_id are required'}), 400

        try:
            quantity = int(quantity)
            if quantity < 1:
                return jsonify({'error': 'quantity must be at least 1'}), 400
        except (TypeError, ValueError):
            return jsonify({'error': 'quantity must be a positive integer'}), 400

        try:
            cursor = mysql.connection.cursor()
            sql = """
            INSERT INTO Cart_Item (cart_id, item_id, quantity, customization_note)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (cart_id, item_id, quantity, customization_note))
            mysql.connection.commit()
            cursor.close()
            return jsonify({'message': 'Item added to cart successfully'}), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500