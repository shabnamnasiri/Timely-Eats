import os
import pymysql
pymysql.install_as_MySQLdb()

from flask import Flask, session, redirect, render_template
from flask_mysqldb import MySQL
from app.auth.auth import login_required, role_required
from app.auth.login.Sign_in import register_login_routes
from app.auth.login.Sign_up import register_register_routes
from app.customer.scan import register_scan_routes
from app.customer.menu import register_menu_routes
from app.customer.add_item import register_add_item_routes
from app.customer.review import register_review_routes
from app.customer.cart import register_customer_cart_routes
from app.customer.place_order import register_customer_place_order_routes
from app.admin.add_menu import register_admin_add_menu_routes
from app.admin.add_staff import register_admin_add_staff_routes
from app.staff.api.staff_api import register_staff_api
from app.staff.session_routes import register_session_routes
from app.customer.profile import register_profile_routes
from app.customer.order_history import register_order_history_routes
from app.customer.loyalty import register_loyalty_routes
from app.staff.orders import register_staff_order_routes
from app.staff.order_hist import register_staff_order_history_routes
from app.admin.orders import register_admin_order_routes
from app.admin.reports import register_admin_report_routes
from app.admin.customer import register_admin_customer_routes
template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "templates")
static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "static")
app = Flask(__name__, template_folder=template_path, static_folder=static_path)
app.secret_key = "secret_key_123"
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '22703380'
app.config['MYSQL_DB'] = 'timlyeats'
app.config['MYSQL_PORT'] = 3306

mysql = MySQL(app)

register_staff_order_routes(app, mysql)
register_login_routes(app, mysql)
register_register_routes(app, mysql)
register_menu_routes(app, mysql)
register_scan_routes(app, mysql)
register_add_item_routes(app, mysql)
register_review_routes(app, mysql)
register_customer_cart_routes(app, mysql)
register_admin_add_menu_routes(app, mysql)
register_customer_place_order_routes(app, mysql)
register_admin_add_staff_routes(app, mysql)
register_staff_api(app, mysql)
register_session_routes(app, mysql)
register_profile_routes(app, mysql)
register_order_history_routes(app, mysql)
register_loyalty_routes(app, mysql)
register_staff_order_history_routes(app, mysql)
register_admin_order_routes(app, mysql)
register_admin_report_routes(app, mysql)
register_admin_customer_routes(app, mysql)
@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/Customer/Menu")
    return redirect("/signin")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)