import os
import pymysql
pymysql.install_as_MySQLdb()

from flask import Flask, session, redirect, render_template
from flask_mysqldb import MySQL
from app.auth.auth import login_required, role_required
from app.auth.login.Sign_in import register_login_routes
from app.auth.login.Sign_up import register_register_routes
from app.auth.login.forgot_password import register_forgotpassword_routes
from app.customer.menu import register_menu_routes
from app.customer.add_item import register_add_item_routes
from app.customer.review import register_review_routes
from app.customer.cart import register_customer_cart_routes
from app.admin.add_menu import register_admin_add_menu_routes
from app.admin.add_staff import register_admin_add_staff_routes
from app.staff.api.staff_api import register_staff_api
from app.staff.session_routes import register_session_routes
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
register_forgotpassword_routes(app, mysql)
register_menu_routes(app, mysql)
register_add_item_routes(app, mysql)
register_review_routes(app, mysql)
register_customer_cart_routes(app, mysql)
register_admin_add_menu_routes(app, mysql)
register_admin_add_staff_routes(app, mysql)
register_staff_api(app, mysql)
register_session_routes(app, mysql)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/signin")

@app.route('/staff/orders')
def staff_orders():
    return render_template('EmpOrder.html')

if __name__ == "__main__":
    app.run(debug=True)