from flask import render_template, redirect, session
import MySQLdb.cursors

def register_customer_cart_routes(app, mysql):

    # ---------------- CART PAGE ----------------
    @app.route('/Customer/Cart')
    def customer_cart():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        user_id = session.get('user_id')
        if not user_id:
            return "User not logged in", 401

        cursor.execute("""
            SELECT * FROM cart
            WHERE user_id = %s AND status='open'
            ORDER BY cart_id DESC LIMIT 1
        """, (user_id,))
        cart = cursor.fetchone()

        if not cart:
            return render_template('Cart.html', cart_items=[], cart_total=0,
                                   table_number="—", loyalty_points=0,
                                   loyalty_progress=0, points_to_next_reward=100,
                                   loyalty_discount='5.00',
                                   loyalty_discount_active=False,
                                   points_earned=0)

        cursor.execute("""
            SELECT ci.cart_item_id AS id,
                   ci.quantity,
                   ci.customization_note AS note,
                   m.name, m.category, m.price
            FROM cart_item ci
            JOIN item m ON ci.item_id = m.item_id
            WHERE ci.cart_id = %s
        """, (cart['cart_id'],))

        rows = cursor.fetchall()

        cart_items = []
        for r in rows:
            cart_items.append({
                "id": r["id"],
                "name": r["name"],
                "category": r["category"],
                "price": float(r["price"]),
                "quantity": r["quantity"],
                "note": r["note"],
                "customisations": [r["note"]] if r["note"] else []
            })

        cart_total = sum(i["price"] * i["quantity"] for i in cart_items)
        points_earned = int(cart_total)

        return render_template("Cart.html",
                               cart_items=cart_items,
                               cart_total=cart_total,
                               table_number="—",
                               loyalty_points=session.get("loyalty_points", 0),
                               loyalty_progress=0,
                               points_to_next_reward=100,
                               loyalty_discount="5.00",
                               loyalty_discount_active=False,
                               points_earned=points_earned)

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

        return redirect("/Customer/Cart")

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

        return redirect("/Customer/Cart")

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

        return redirect("/Customer/Cart")