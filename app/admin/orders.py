from flask import render_template, session

from app.admin.helpers import admin_required, get_admin_user
from app.staff.orders import get_orders, get_sessions


def register_admin_order_routes(app, mysql):

    @app.route("/admin/orders")
    def admin_orders():
        guard = admin_required()
        if guard:
            return guard

        orders = get_orders(mysql)
        sessions, closed_sessions = get_sessions(mysql)

        stats = {
            "active_orders": len(orders),
            "pending_orders": sum(1 for o in orders if o["status"] == "pending"),
            "preparing_orders": sum(1 for o in orders if o["status"] == "preparing"),
            "ready_orders": sum(1 for o in orders if o["status"] == "ready"),
        }

        return render_template(
            "admin_orders.html",
            orders=orders,
            stats=stats,
            sessions=sessions,
            closed_sessions=closed_sessions,
            user=get_admin_user(mysql),
            admin_name=session.get("username", "Admin"),
        )
