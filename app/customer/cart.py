from flask import render_template, redirect, session, flash, request
import MySQLdb.cursors


def register_customer_cart_routes(app, mysql):

    # ---------------- CART PAGE ----------------
    @app.route('/Customer/Cart')
    def customer_cart():
        user_id = session.get('user_id')
        if not user_id:
            return redirect('/signin')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Get loyalty points from DB ✅
        cursor.execute("""
            SELECT loyalty_point FROM User WHERE user_id = %s
        """, (user_id,))
        user_data = cursor.fetchone()
        loyalty_points = user_data['loyalty_point'] if user_data else 0

        # Get active cart
        cursor.execute("""
            SELECT * FROM cart
            WHERE user_id = %s AND status='open'
            ORDER BY cart_id DESC LIMIT 1
        """, (user_id,))
        cart = cursor.fetchone()

        # Calculate loyalty values ✅
        loyalty_progress      = loyalty_points % 100
        points_to_next_reward = 100 - loyalty_progress if loyalty_progress != 0 else 0
        loyalty_discount      = (loyalty_points // 100) * 5  # 100pts = $5
        loyalty_discount_active = loyalty_points >= 100       # True if enough to redeem

        if not cart:
            cursor.close()
            return render_template('Cart.html',
                                   cart_items=[],
                                   cart_total=0,
                                   table_number=session.get('table_number', '—'),
                                   loyalty_points=loyalty_points,
                                   loyalty_progress=loyalty_progress,
                                   points_to_next_reward=points_to_next_reward,
                                   loyalty_discount=loyalty_discount,
                                   loyalty_discount_active=loyalty_discount_active,
                                   points_earned=0)

        cursor.execute("""
            SELECT ci.cart_item_id,
                   ci.quantity,
                   ci.customization_note,
                   i.name,
                   i.category,
                   i.price
            FROM cart_item ci
            JOIN item i ON ci.item_id = i.item_id
            WHERE ci.cart_id = %s
        """, (cart['cart_id'],))

        rows = cursor.fetchall()
        cursor.close()

        cart_items = []
        for r in rows:
            cart_items.append({
                "cart_item_id":       r["cart_item_id"],
                "name":               r["name"],
                "category":           r["category"],
                "price":              float(r["price"]),
                "quantity":           r["quantity"],
                "customization_note": r["customization_note"],
                "customisations":     [r["customization_note"]] if r["customization_note"] else []
            })

        cart_total    = sum(i["price"] * i["quantity"] for i in cart_items)
        points_earned = int(cart_total * 0.10)  # ✅ 10% of total, not 100%

        return render_template("Cart.html",
                               cart_items=cart_items,
                               cart_total=cart_total,
                               table_number=session.get('table_number', '—'),
                               loyalty_points=loyalty_points,          # ✅ from DB
                               loyalty_progress=loyalty_progress,      # ✅ calculated
                               points_to_next_reward=points_to_next_reward,  # ✅
                               loyalty_discount=loyalty_discount,      # ✅ in $
                               loyalty_discount_active=loyalty_discount_active,  # ✅ True/False
                               points_earned=points_earned)            # ✅ 10% preview

    # ---------------- INCREASE ----------------
    @app.route("/cart/increase/<int:item_id>", methods=["POST"])
    def increase_item(item_id):
        cursor = mysql.connection.cursor()
        cursor.execute("""
            UPDATE cart_item
            SET quantity = quantity + 1
            WHERE cart_item_id = %s
        """, (item_id,))
        mysql.connection.commit()
        cursor.close()
        return redirect('/Customer/Cart')

    # ---------------- DECREASE ----------------
    @app.route("/cart/decrease/<int:item_id>", methods=["POST"])
    def decrease_item(item_id):
        cursor = mysql.connection.cursor()
        cursor.execute("""
            UPDATE cart_item
            SET quantity = quantity - 1
            WHERE cart_item_id = %s
        """, (item_id,))
        cursor.execute("""
            DELETE FROM cart_item
            WHERE cart_item_id = %s AND quantity <= 0
        """, (item_id,))
        mysql.connection.commit()
        cursor.close()
        return redirect('/Customer/Cart')

    # ---------------- REMOVE ----------------
    @app.route("/cart/remove/<int:item_id>", methods=["POST"])
    def remove_item(item_id):
        cursor = mysql.connection.cursor()
        cursor.execute("""
            DELETE FROM cart_item
            WHERE cart_item_id = %s
        """, (item_id,))
        mysql.connection.commit()
        cursor.close()
        return redirect('/Customer/Cart')

    # ---------------- SAVE NOTES ----------------
    @app.route('/cart/save_notes', methods=['POST'])
    def save_notes():
        cursor = mysql.connection.cursor()
        for key, value in request.form.items():
            if key.startswith('note_'):
                cart_item_id = key.split('_', 1)[1]
                note = value.strip()
                cursor.execute("""
                    UPDATE cart_item
                    SET customization_note = %s
                    WHERE cart_item_id = %s
                """, (note if note else None, cart_item_id))
        mysql.connection.commit()
        cursor.close()
        flash('Preferences saved!', 'success')
        return redirect('/Customer/Cart')