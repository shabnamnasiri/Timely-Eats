from flask import jsonify, session


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
            AND (
                (o.status IN ('pending', 'preparing') AND o.notified = 0)
                OR
                (o.status IN ('ready', 'closed') AND o.ready_notified = 0)
            )
            GROUP BY o.order_id, o.status
            ORDER BY o.timestamp DESC
            LIMIT 5
        """, (user_id,))
        orders = cursor.fetchall()

        if orders:
            non_ready = [o[0] for o in orders if o[1] not in ('ready', 'closed')]
            if non_ready:
                ph = ", ".join(["%s"] * len(non_ready))
                cursor.execute(
                    f"UPDATE orders SET notified = 1 WHERE order_id IN ({ph})",
                    non_ready
                )

            ready = [o[0] for o in orders if o[1] in ('ready', 'closed')]
            if ready:
                ph = ", ".join(["%s"] * len(ready))
                cursor.execute(
                    f"UPDATE orders SET ready_notified = 1 WHERE order_id IN ({ph})",
                    ready
                )

            mysql.connection.commit()

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
            "ready":     "Your order is ready! Enjoy your meal 🍽️",
            "closed":    "Your order is ready! Enjoy your meal 🍽️",
        }.get(status, "Order status updated.")