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
            flash("No table session found. Please scan the QR code on your table.", "warning")
            return redirect('/signin')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

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
        order_status = 'pending'

        if payment_method == 'cash':
            payment_status = 'pending'
        elif payment_method == 'card':
            payment_status = 'confirmed'
        else:
            flash("Invalid payment method selected.", "danger")
            cursor.close()
            return redirect('/Customer/Cart')

        # Check if redeeming points
        redeem = request.form.get('redeem_points') == 'on'

        # Get current loyalty points
        cursor.execute("""
            SELECT loyalty_point FROM User WHERE user_id = %s
        """, (user_id,))
        user = cursor.fetchone()
        current_points = user['loyalty_point'] if user else 0

        # Calculate discount if redeeming
        discount = 0
        if redeem and current_points >= 100:
            # how many full 100-point blocks does the user have?
            redeemable_blocks = current_points // 100
            discount = redeemable_blocks * 5  # 100 points = $5
            discount = min(discount, total_amount)  # can't discount more than total

        discounted_total = total_amount - discount

        # Calculate points earned — 10% of discounted total
        points_earned = int(discounted_total * 0.10)
        cursor.execute("""
            SELECT MAX(i.preparation_time) AS max_prep
            FROM cart_item ci
            JOIN item i ON i.item_id = ci.item_id
            WHERE ci.cart_id = %s
        """, (cart_id,))

        max_prep = cursor.fetchone()["max_prep"] or 10

        cursor.execute("""
            INSERT INTO orders
            (user_id, cart_id, timestamp, preparation_time, status, total_amount, session_id)
            VALUES (%s, %s, %s, %s, 'pending', %s, %s)
        """, (
            user_id,
            cart_id,
            datetime.now(),
            max_prep,
            discounted_total,
            session_id
        ))
        order_id = cursor.lastrowid

        # Insert order_details
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

        # Insert payment
        cursor.execute("""
            INSERT INTO payment (order_id, payment_method, payment_status, date)
            VALUES (%s, %s, %s, %s)
        """, (order_id, payment_method, payment_status, datetime.now()))

        # Mark cart as closed
        cursor.execute("""
            UPDATE cart SET status = 'closed'
            WHERE cart_id = %s
        """, (cart_id,))

        # 🔥 FIX 1: Explicitly drop items from cart_item table to empty out the cart content fields
        cursor.execute("""
            DELETE FROM cart_item 
            WHERE cart_id = %s
        """, (cart_id,))

        points_used = 0
        # Update loyalty points
        if redeem and current_points >= 100:
            points_used = (current_points // 100) * 100  # deduct full blocks only
            cursor.execute("""
                UPDATE User
                SET loyalty_point = loyalty_point - %s + %s
                WHERE user_id = %s
            """, (points_used, points_earned, user_id))
        else:
            cursor.execute("""
                UPDATE User
                SET loyalty_point = loyalty_point + %s
                WHERE user_id = %s
            """, (points_earned, user_id))

        # Update session so cart page shows new points immediately
        session['loyalty_points'] = current_points - (
            points_used if redeem and current_points >= 100 else 0) + points_earned

        mysql.connection.commit()
        cursor.close()

        if redeem and discount > 0:
            flash(f"Order placed! ${discount:.2f} discount applied. You earned {points_earned} points.", "success")
        else:
            flash(f"Order placed! You earned {points_earned} loyalty points.", "success")

        # ✅ FIX 2: Dynamic redirect straight to the custom customer order history panel
        return redirect('/customer/order_history')