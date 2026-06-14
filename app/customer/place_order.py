from flask import jsonify, render_template, redirect, session, flash, request
from datetime import datetime
import MySQLdb.cursors


def register_customer_place_order_routes(app, mysql):

    @app.route('/Customer/PlaceOrder', methods=['POST'])
    def place_order():
        user_id = session.get('user_id')
        if not user_id:
            return redirect('/signin')

        payment_method = request.form.get('payment_method')
        session_id = session.get('table_session_id')

        if not session_id:
            flash("No table session found. Please scan the QR code on your table.", "warning")
            return redirect('/signin')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        cursor.execute("""
            SELECT session_id, status
            FROM table_session
            WHERE session_id = %s AND status IN ('active', 'ordered')
        """, (session_id,))
        table_session = cursor.fetchone()

        if not table_session:
            flash("Your table session is no longer valid. Please scan the QR code again.", "warning")
            session.pop('table_session_id', None)
            cursor.close()
            return redirect('/signin')

        # Get active cart
        cursor.execute("""
            SELECT * FROM cart
            WHERE user_id = %s AND status = 'open'
            ORDER BY cart_id DESC
            LIMIT 1
        """, (user_id,))
        cart = cursor.fetchone()

        if not cart:
            flash("No active cart found.", "warning")
            cursor.close()
            return redirect('/Customer/Cart')

        cart_id = cart['cart_id']

        # Fetch cart items
        cursor.execute("""
            SELECT ci.item_id, ci.quantity, ci.customization_note, i.price
            FROM cart_item ci
            JOIN item i ON ci.item_id = i.item_id
            WHERE ci.cart_id = %s
        """, (cart_id,))
        cart_items = cursor.fetchall()

        if not cart_items:
            flash("Your cart is empty.", "warning")
            cursor.close()
            return redirect('/Customer/Cart')

        total_amount = sum(item['quantity'] * float(item['price']) for item in cart_items)

        # Get loyalty points
        cursor.execute("SELECT loyalty_point FROM user WHERE user_id = %s", (user_id,))
        user_row = cursor.fetchone()
        loyalty_points = user_row['loyalty_point'] if user_row else 0

        # Apply loyalty discount if user toggled redeem (100 pts = $1 discount)
        if session.get('redeem_points') and loyalty_points >= 100:
            loyalty_discount = float(session.get('loyalty_discount', 0))
            total_amount = max(0, total_amount - loyalty_discount)

            points_used = int(loyalty_discount * 100)
            cursor.execute("""
                UPDATE user SET loyalty_point = loyalty_point - %s
                WHERE user_id = %s
            """, (points_used, user_id))

            session.pop('redeem_points', None)
            session.pop('loyalty_discount', None)

        if payment_method not in ('cash', 'card'):
            flash("Invalid payment method selected.", "danger")
            cursor.close()
            return redirect('/Customer/Cart')

        cursor.execute("""
            SELECT MAX(i.preparation_time) AS max_prep
            FROM cart_item ci
            JOIN item i ON i.item_id = ci.item_id
            WHERE ci.cart_id = %s
        """, (cart_id,))
        max_prep = cursor.fetchone()["max_prep"] or 10

        order_time = datetime.now()

        # Insert order
        cursor.execute("""
            INSERT INTO orders
            (user_id, cart_id, timestamp, preparation_time, status, total_amount, session_id)
            VALUES (%s, %s, %s, %s, 'pending', %s, %s)
        """, (user_id, cart_id, order_time, max_prep, total_amount, session_id))
        order_id = cursor.lastrowid

        # Insert order_details
        for item in cart_items:
            cursor.execute("""
                INSERT INTO order_details (order_id, item_id, quantity, customization_note)
                VALUES (%s, %s, %s, %s)
            """, (order_id, item['item_id'], item['quantity'], item['customization_note']))

        # Insert payment
        cursor.execute("""
            INSERT INTO payment (order_id, payment_method, payment_status, date)
            VALUES (%s, %s, %s, %s)
        """, (order_id, payment_method, 'confirmed', order_time))

        # Close current cart
        cursor.execute("UPDATE cart SET status = 'closed' WHERE cart_id = %s", (cart_id,))

        # Open fresh cart for continued ordering
        cursor.execute("INSERT INTO cart (user_id, status) VALUES (%s, 'open')", (user_id,))

        # Award loyalty points (1 pt per $1 spent after discount)
        points_earned = int(total_amount)
        cursor.execute("""
            UPDATE user SET loyalty_point = loyalty_point + %s
            WHERE user_id = %s
        """, (points_earned, user_id))

        # Mark session as 'ordered' on first order, bump updated_at
        cursor.execute("""
            UPDATE table_session
            SET status = CASE WHEN status = 'active' THEN 'ordered' ELSE status END,
                updated_at = %s
            WHERE session_id = %s
        """, (order_time, session_id))

        mysql.connection.commit()
        cursor.close()

        flash("Order placed successfully!", "success")
        return redirect('/customer/order_history')


    @app.route('/apply_loyalty', methods=['POST'])
    def apply_loyalty():
        data = request.get_json()
        redeem = data.get('redeem', False)

        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not logged in'}), 401

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        cursor.execute("SELECT loyalty_point FROM user WHERE user_id = %s", (user_id,))
        user_row = cursor.fetchone()
        loyalty_points = user_row['loyalty_point'] if user_row else 0

        cursor.execute("""
            SELECT ci.quantity, i.price
            FROM cart_item ci
            JOIN item i ON ci.item_id = i.item_id
            WHERE ci.cart_id = (
                SELECT cart_id FROM cart
                WHERE user_id = %s AND status = 'open'
                ORDER BY cart_id DESC
                LIMIT 1
            )
        """, (user_id,))
        items = cursor.fetchall()
        cursor.close()

        if not items:
            return jsonify({'success': False, 'error': 'No open cart found'}), 400

        order_total = sum(row['quantity'] * float(row['price']) for row in items)

        discount = 0
        if redeem and loyalty_points >= 100:
            discount = min(loyalty_points // 100, order_total)  # can't exceed order total
            session['redeem_points'] = True
            session['loyalty_discount'] = discount
        else:
            session.pop('redeem_points', None)
            session.pop('loyalty_discount', None)

        new_total = max(0, order_total - discount)

        return jsonify({
            'success': True,
            'discount': round(discount, 2),
            'new_total': round(new_total, 2),
            'order_total': round(order_total, 2)
        })