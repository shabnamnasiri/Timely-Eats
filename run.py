import os
import pymysql

pymysql.install_as_MySQLdb()

from flask import Flask, session
from flask_socketio import join_room

from app.extensions import socketio, mysql

# =========================
# APP SETUP
# =========================

template_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "app",
    "templates"
)

static_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "app",
    "static"
)

app = Flask(
    __name__,
    template_folder=template_path,
    static_folder=static_path
)

app.secret_key = os.getenv("SECRET_KEY", "secret_key_123")

# =========================
# MYSQL CONFIG
# =========================

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "timlyeats"
app.config["MYSQL_PORT"] = 3306
app.config["MYSQL_AUTOCOMMIT"] = True

# =========================
# INITIALIZE EXTENSIONS
# =========================

mysql.init_app(app)

socketio.init_app(
    app,
    manage_session=False,
    cors_allowed_origins="*",
    async_mode="threading"
)

# =========================
# IMPORT ROUTES AFTER INIT
# =========================

from app.customer.order_notifications import register_notification_routes
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
from app.staff.orders import (
    register_staff_order_routes,
    get_orders,
    get_sessions
)
from app.auth.login.forgot_password import register_forgotpassword_routes

# =========================
# REGISTER ROUTES
# =========================

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
register_staff_order_routes(app, mysql)
register_forgotpassword_routes(app, mysql)
register_notification_routes(app, mysql)

# =========================
# SOCKET CONNECTIONS
# =========================

@socketio.on("connect")
def connect():
    user_id = session.get("user_id")
    role_id = session.get("role_id")

    print(f"[SOCKET CONNECT] user={user_id} role={role_id}")

    if user_id:
        join_room(f"user_{user_id}")

    if role_id == 2:
        join_room("staff")

    if role_id == 1:
        join_room("admin")

# =========================
# REAL-TIME STAFF DASHBOARD
# =========================

def push_staff_dashboard():
    while True:
        socketio.sleep(10)

        try:
            with app.app_context():

                orders = get_orders(mysql)
                sessions, closed_sessions = get_sessions(mysql)

                # Do not compute average wait time (removed from UI)
                stats = {
                    "active_orders": len(orders),
                    "pending_orders": sum(
                        1 for o in orders if o["status"] == "pending"
                    ),
                    "preparing_orders": sum(
                        1 for o in orders if o["status"] == "preparing"
                    ),
                    "ready_orders": sum(
                        1 for o in orders if o["status"] == "ready"
                    ),
                }

                socketio.emit(
                    "dashboard_refresh",
                    {
                        "orders": orders,
                        "stats": stats,
                        "sessions": sessions,
                        "closed_sessions": closed_sessions,
                    },
                    to="staff"
                )

        except Exception as e:
            print("[push_staff_dashboard ERROR]", e)

# =========================
# START BACKGROUND TASK
# =========================

socketio.start_background_task(push_staff_dashboard)

# =========================
# RUN SERVER
# =========================

if __name__ == "__main__":
    socketio.run(app, debug=True)