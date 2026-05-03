from flask import render_template, redirect, session, flash, request
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
            flash("No table session found. Please scan the QR code again.", "warning")
            return redirect('/scan-required')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # ✅ 'open' to match cart.py
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

        if payment_method == 'cash':
            order_status = 'pending cash'
            payment_status = 'pending'
        elif payment_method == 'card':
            order_status = 'pending payment'
            payment_status = 'pending'
        else:
            flash("Invalid payment method selected.", "danger")
            cursor.close()
            return redirect('/Customer/Cart')

        cursor.execute("""
            INSERT INTO orders
            (user_id, cart_id, timestamp, status, payment_method, total_amount, session_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            cart_id,
            datetime.now(),
            order_status,
            payment_method,
            total_amount,
            session_id
        ))
        order_id = cursor.lastrowid

        for item in cart_items:
            cursor.execute("""
                INSERT INTO order_details
                (order_id, item_id, quantity, customization_note)
                VALUES (%s, %s, %s, %s)
            """, (
                order_id,
                item['item_id'],
                item['quantity'],
                item['customization_note']
            ))

        cursor.execute("""
            INSERT INTO payment (order_id, payment_status, date)
            VALUES (%s, %s, %s)
        """, (order_id, payment_status, datetime.now()))

        # ✅ match whatever status your DB uses for completed carts
        cursor.execute("""
            UPDATE cart SET status = 'closed'
            WHERE cart_id = %s
        """, (cart_id,))

        mysql.connection.commit()
        cursor.close()

        flash("Order placed successfully!", "success")
        return redirect('/order/success')

    @app.route('/order/success')
    def order_success():
        return "Order placed successfully!"

