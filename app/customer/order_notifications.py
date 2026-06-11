from flask import jsonify, session, flash, redirect, request
from app.extensions import socketio


def register_notification_routes(app, mysql):

    @app.route("/notifications/order-status-json")
    def order_status_json():
        user_id = session.get("user_id")
        if not user_id:
            return jsonify([])

        cursor = mysql.connection.cursor()
        cursor.execute("""
        SELECT o.order_id, o.status,
            GROUP_CONCAT(i.name ORDER BY i.name SEPARATOR ', ') AS items
        FROM orders o
        JOIN order_details od ON od.order_id = o.order_id
        JOIN item i ON i.item_id = od.item_id
        WHERE o.user_id = %s
        AND o.status IN ('pending', 'preparing', 'ready', 'closed')
        GROUP BY o.order_id, o.status
        ORDER BY o.timestamp DESC
        LIMIT 5
    """, (user_id,))
        orders = cursor.fetchall()
        cursor.close()

        return jsonify([{
            "order_id": o[0],
            "status":   o[1],
            "items":    o[2] or "",
            "message":  _status_message(o[1])
        } for o in orders])


    def _status_message(status):
        return {
            "pending":   "Your order has been received!",
            "preparing": "Your order is being prepared!",
            "ready":     "Your order is ready! Enjoy your meal.",
        }.get(status, "Order status updated.")

