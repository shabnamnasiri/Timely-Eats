import os
from flask import Flask, render_template, session, redirect, send_file
from app.auth.auth import login_required, role_required
from app.auth.login.Sign_in import register_login_routes
from app.auth.login.Sign_up import register_register_routes
from app.customer.menu import register_menu_routes
from app.staff.add_menu import register_add_menu_routes
import pymysql
import qrcode
import uuid
from io import BytesIO
from datetime import datetime
pymysql.install_as_MySQLdb()
from flask import Flask, session, redirect
from flask_mysqldb import MySQL
from app.staff.api.staff_api import register_staff_api
from app.staff.qr.session_routes import register_session_routes



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
register_add_menu_routes(app, mysql)
register_staff_api(app, mysql)
register_session_routes(app, mysql)

@app.route("/")
def home():
    return "Welcome to TimelyEats!"

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

@app.route('/test-db')
def test_db():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT 1")
    return "DB Connected!"

@app.route('/debug-static')
def debug_static():
    return app.static_folder

@app.route('/staff/orders')
def staff_orders():
    return render_template('EmpOrder.html')


if __name__ == "__main__":
    app.run(debug=True)