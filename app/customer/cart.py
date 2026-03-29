from flask import render_template, redirect, session

def register_customer_cart_routes(app, mysql):
    @app.route("/customer/cart", methods=["GET"])
    def customer_cart():
        if "user_id" not in session:
            return redirect("/signin")
        return render_template("Cart.html")