import os
from flask import Flask, session, redirect
from flask_mysqldb import MySQL
from app.auth.auth import login_required, role_required
from app.auth.login.Sign_in import register_login_routes
from app.auth.login.Sign_up import register_register_routes
from app.customer.menu import register_menu_routes
from app.staff.add_menu import register_add_menu_routes

# Абсолютный путь к папке templates внутри app/
template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "templates")

app = Flask(__name__, template_folder=template_path)
app.secret_key = "secret_key_123"

# ----------------- MySQL config -----------------
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'timlyeats'
app.config['MYSQL_PORT'] = 3306

mysql = MySQL(app)

# ----------------- Подключаем маршруты -----------------
register_login_routes(app, mysql)
register_register_routes(app, mysql)
register_menu_routes(app, mysql)
register_add_menu_routes(app, mysql)

# ----------------- Пример маршрутов -----------------
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

# ----------------- Запуск -----------------
if __name__ == "__main__":
    app.run(debug=True)