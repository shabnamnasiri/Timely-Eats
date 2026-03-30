from flask import Blueprint, request,session,redirect,flash

add_item_bp = Blueprint('add_item', __name__)

def register_add_item_routes(app, mysql):
    @app.route("/add_to_cart", methods=["POST"])
    def add_to_cart():
        if "user_id" not in session:
            return redirect("/signin")

        user_id = session["user_id"]
        item_id = request.form["item_id"]
        quantity = 1

        cur = mysql.connection.cursor()

        # 1. Get active cart for user
        cur.execute("SELECT cart_id FROM cart WHERE user_id=%s AND status='open'", (user_id,))
        cart = cur.fetchone()

        if cart:
            cart_id = cart[0]
        else:
            # Create new cart
            cur.execute("INSERT INTO cart (user_id, status) VALUES (%s, 'open')", (user_id,))
            mysql.connection.commit()
            cart_id = cur.lastrowid

        # 2. Check if item already in cart
        cur.execute("SELECT cart_item_id, quantity FROM cart_item WHERE cart_id=%s AND item_id=%s", (cart_id, item_id))
        cart_item = cur.fetchone()

        if cart_item:
            # Update quantity
            new_quantity = cart_item[1] + quantity
            cur.execute("UPDATE cart_item SET quantity=%s WHERE cart_item_id=%s", (new_quantity, cart_item[0]))
        else:
            # Insert new item
            cur.execute("INSERT INTO cart_item (cart_id, item_id, quantity) VALUES (%s, %s, %s)", (cart_id, item_id, quantity))

        mysql.connection.commit()
        cur.close()
        flash("Item added to your cart!", "success")
        return redirect("/menu")