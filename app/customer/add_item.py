from flask import Blueprint, request, session, redirect, flash

add_item_bp = Blueprint('add_item', __name__)

def register_add_item_routes(app, mysql):
    @app.route("/add_to_cart", methods=["POST"])
    def add_to_cart():
        #get data from form
        session_id = session.get('table_session_id')
        user_id = session["user_id"]
        item_id = request.form["item_id"]
        quantity = 1
        
        cur = mysql.connection.cursor()

        #get active cart for user linked to the session
        cur.execute("SELECT cart_id FROM cart WHERE user_id=%s AND status='open'", (user_id))
        cart = cur.fetchone()
        #if cart exist use else create new cart
        if cart:
            cart_id = cart[0]
        else:
            cur.execute("INSERT INTO cart (user_id, status) VALUES (%s, 'open')", (user_id))
            mysql.connection.commit()
            cart_id = cur.lastrowid

        #check if item is already in the cart
        cur.execute("SELECT cart_item_id, quantity FROM cart_item WHERE cart_id=%s AND item_id=%s", (cart_id, item_id))
        cart_item = cur.fetchone()
        #if item is already in cart update quantity else insert new item
        if cart_item:
            new_quantity = cart_item[1] + quantity
            cur.execute("UPDATE cart_item SET quantity=%s WHERE cart_item_id=%s", (new_quantity, cart_item[0]))
        else:
            cur.execute("INSERT INTO cart_item (cart_id, item_id, quantity) VALUES (%s, %s, %s)", (cart_id, item_id, quantity))

        mysql.connection.commit()
        cur.close()
        flash("Item added to your cart!", "success")
        return redirect("/menu")