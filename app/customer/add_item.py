from flask import Blueprint, request, session, redirect, flash

add_item_bp = Blueprint('add_item', __name__)

def register_add_item_routes(app, mysql):
    @app.route("/add_to_cart", methods=["POST"])
    def add_to_cart():
        session_id = request.form.get("session_id") or session.get("table_session_id")
        if session_id:
            session["table_session_id"] = str(session_id)

        if "user_id" not in session:
            return redirect(f"/signin?next=/menu?session_id={session_id}")

        user_id = session["user_id"]
        item_id = request.form["item_id"]
        quantity = 1

        cur = mysql.connection.cursor()

        # 1. Get active cart for user linked to session
        cur.execute("SELECT cart_id FROM cart WHERE user_id=%s AND session_id=%s AND status='open'", (user_id, session_id))
        cart = cur.fetchone()

        if cart:
            cart_id = cart[0]
        else:
            # Create new cart
            cur.execute("INSERT INTO cart (user_id, session_id, status) VALUES (%s, %s, 'open')", (user_id, session_id))
            mysql.connection.commit()
            cart_id = cur.lastrowid

        # 2. Check if item already in cart
        cur.execute("SELECT cart_item_id, quantity FROM cart_item WHERE cart_id=%s AND item_id=%s", (cart_id, item_id))
        cart_item = cur.fetchone()

        if cart_item:
            new_quantity = cart_item[1] + quantity
            cur.execute("UPDATE cart_item SET quantity=%s WHERE cart_item_id=%s", (new_quantity, cart_item[0]))
        else:
            cur.execute("INSERT INTO cart_item (cart_id, item_id, quantity) VALUES (%s, %s, %s)", (cart_id, item_id, quantity))

        mysql.connection.commit()
        cur.close()
        flash("Item added to your cart!", "success")
        return redirect(f"/menu?session_id={session_id}")