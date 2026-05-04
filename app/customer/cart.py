from flask import render_template, session
import MySQLdb.cursors


def register_customer_cart_routes(app, mysql):
    @app.route('/Customer/Cart')
    def customer_cart():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        table_session_id = session.get('table_session_id')

        user_id = session.get('user_id')
        if not user_id:
            return "User not logged in", 401

        table_number = "-"

        if table_session_id:
            cursor.execute("""
                SELECT table_number FROM Table_Session
                WHERE session_id = %s AND status = 'active'
            """, (table_session_id,))
            table_session = cursor.fetchone()
            if table_session:
                table_number = table_session['table_number']

        # Get latest active cart for user
        cursor.execute("""
            SELECT * FROM cart
            WHERE user_id = %s AND status='open'
            ORDER BY cart_id DESC LIMIT 1
        """, (user_id,))
        cart = cursor.fetchone()

        if not cart:
            return render_template('Cart.html',
                cart_items=[],
                cart_total=0,
                table_number=table_number,
                table_session_id=table_session_id,
                loyalty_points=0,
                loyalty_progress=0,
                points_to_next_reward=100,
                loyalty_discount='5.00',
                loyalty_discount_active=False,
                points_earned=0,
                order_placed=False,
                order_number=None,
            )

        # Get cart items with menu info
        cursor.execute("""
            SELECT ci.cart_item_id AS id, ci.quantity,
                ci.customization_note AS note,
                m.item_id, m.name, m.category, m.price
            FROM cart_item ci
            JOIN item m ON ci.item_id = m.item_id
            WHERE ci.cart_id = %s
        """, (cart['cart_id'],))
        raw_items = cursor.fetchall()

        # Shape items to match what the template expects
        cart_items = [
            {
                'id': row['id'],
                'item_id': row['item_id'],
                'name': row['name'],
                'category': row['category'],
                'price': float(row['price']),
                'quantity': row['quantity'],
                'note': row['note'],
                'customisations': [],
            }
            for row in raw_items
        ]
        cart_total = sum(i['price'] * i['quantity'] for i in cart_items)
        points_earned = int(cart_total)   # 1 pt per $1 - adjust to your logic

        # Loyalty data placeholder until real queries are added
        loyalty_points = session.get('loyalty_points', 0)
        points_to_next = max(0, 100 - (loyalty_points % 100))
        loyalty_progress = loyalty_points % 100
        loyalty_discount = '5.00'
        loyalty_discount_active = False

        return render_template('Cart.html',
            cart_items=cart_items,
            cart_total=cart_total,
            table_number=table_number,
            table_session_id=table_session_id,
            loyalty_points=loyalty_points,
            loyalty_progress=loyalty_progress,
            points_to_next_reward=points_to_next,
            loyalty_discount=loyalty_discount,
            loyalty_discount_active=loyalty_discount_active,
            points_earned=points_earned,
            order_placed=session.pop('order_placed', False),
            order_number=session.pop('order_number', None),
        )
