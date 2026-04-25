import os
import pymysql
pymysql.install_as_MySQLdb()
# app.secret_key = os.environ.get("SECRET_KEY")
# app.config['MYSQL_PASSWORD'] = os.environ.get("MYSQL_PASSWORD")


from flask import Flask, session, redirect
from flask_mysqldb import MySQL
from flask import render_template

from app.auth.auth import login_required, role_required
from app.auth.login.Sign_in import register_login_routes
from app.auth.login.Sign_up import register_register_routes
from app.auth.login.forgot_password import register_forgotpassword_routes
from app.customer.menu import register_menu_routes
from app.customer.add_item import register_add_item_routes
from app.customer.review import register_review_routes
from app.admin.add_menu import register_admin_add_menu_routes
from app.admin.add_staff import register_admin_add_staff_routes
from app.customer.cart import register_customer_cart_routes
template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "templates")
static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "static")

app = Flask(__name__, template_folder=template_path, static_folder=static_path)

app.secret_key = "secret_key_123"
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'timlyeats'
app.config['MYSQL_PORT'] = 3306

mysql = MySQL(app)

register_login_routes(app, mysql)
register_register_routes(app, mysql)
register_menu_routes(app, mysql)
register_add_item_routes(app, mysql)
register_review_routes(app, mysql)
register_admin_add_menu_routes(app, mysql)
register_customer_cart_routes(app,mysql)
register_forgotpassword_routes(app, mysql)
register_admin_add_staff_routes(app,mysql)

@app.route("/review")
def review_page():
    return render_template("CustRating.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/signin")

@app.route("/customer")
@role_required(1)
def customer_page():
    return "Customer dashboard"

@app.route("/staff")
@role_required(2)
def staff_page():
    return "Staff dashboard"

@app.route("/admin")
@role_required(3)
def admin_page():
    return "Admin panel"

@app.route("/Customer/Cart")
def cart_page():
    if "user_id" not in session:
        return redirect("/signin")
    return render_template("Cart.html")

if __name__ == "__main__":
    app.run(debug=True)