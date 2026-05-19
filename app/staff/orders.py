from datetime import datetime
from flask import flash, redirect, render_template, request, session
import MySQLdb.cursors


def require_staff():
    """Block access if user is not logged in or not a staff member."""
    if "user_id" not in session:
        return redirect("/signin")
    if session.get("role_id") != 2:
        return "Access denied", 403
    return None


def get_orders(mysql):
    """Fetch all active orders (pending/preparing/ready) from the database."""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
       SELECT
            o.order_id, o.user_id, o.timestamp, o.status,
            o.total_amount, o.session_id, o.preparation_time,
            u.username, ts.table_number,
            p.payment_status, p.payment_method,
            i.name AS item_name, od.quantity, od.customization_note
        FROM orders o
        LEFT JOIN User u ON u.user_id = o.user_id
        LEFT JOIN Table_Session ts ON ts.session_id = o.session_id
        LEFT JOIN payment p ON p.order_id = o.order_id
        LEFT JOIN order_details od ON od.order_id = o.order_id
        LEFT JOIN item i ON i.item_id = od.item_id
        WHERE LOWER(COALESCE(o.status, '')) IN ('pending', 'preparing', 'ready')
        ORDER BY o.timestamp DESC
    """)
    rows = cursor.fetchall()
    cursor.close()

    # Each order can have multiple rows (one per item), so we group them by order_id
    orders = {}
    for row in rows:
        oid = row["order_id"]

        if oid not in orders:
            ts = row["timestamp"]
            prep_time = int(row["preparation_time"] or 10)
            wait_minutes = int(max((datetime.now() - ts).total_seconds(), 0) // 60) if ts else 0
            remaining_minutes = max(prep_time - wait_minutes, 0)

            orders[oid] = {
                "order_id":         oid,
                "session_id":       row["session_id"],
                "table_number":     row["table_number"],
                "customer_name":    row["username"] or f"Customer #{row['user_id']}",
                "status":           (row["status"] or "").strip().lower(),
                "payment_label":    f"{(row['payment_method'] or 'unknown').upper()} - {(row['payment_status'] or 'pending').title()}",
                "total_amount":     float(row["total_amount"] or 0),
                "preparation_time": prep_time,
                "wait_minutes":     wait_minutes,
                "remaining_minutes": remaining_minutes,
                "created_label":    ts.strftime("%Y-%m-%d %H:%M") if ts else "Unknown",
                "lines":            [],
            }

        # Append this row's item to the order
        if row["item_name"]:
            orders[oid]["lines"].append({
                "item": f"{row['quantity'] or 0}x {row['item_name']}",
                "note": (row["customization_note"] or "").strip()
            })
    # Turn the dict into a list and build a readable item summary for each order
    orders = list(orders.values())
    for o in orders:
    # Replace the summary line at the bottom with:
        o["summary"] = ", ".join(l["item"] for l in o["lines"]) if o["lines"] else "No items"
    return orders


def get_sessions(mysql):
    """Fetch all table sessions so staff can see which tables are active."""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT ts.session_id, ts.table_number, ts.status, COUNT(o.order_id) AS order_count
        FROM Table_Session ts
        LEFT JOIN orders o ON o.session_id = ts.session_id
        GROUP BY ts.session_id, ts.table_number, ts.status
        ORDER BY ts.table_number ASC
    """)
    rows = cursor.fetchall()
    cursor.close()
    return rows


def register_staff_order_routes(app, mysql):

    @app.route("/staff/orders")
    def staff_orders():
        if (block := require_staff()):
            return block

        orders = get_orders(mysql)
        sessions = get_sessions(mysql)

        # Count orders per status for the dashboard stats bar
        stats = {
            "active_orders":    len(orders),
            "pending_orders":   sum(1 for o in orders if o["status"] == "pending"),
            "preparing_orders": sum(1 for o in orders if o["status"] == "preparing"),
            "ready_orders":     sum(1 for o in orders if o["status"] == "ready"),
            "avg_wait":         int(sum(o["wait_minutes"] for o in orders) / len(orders)) if orders else 0,
        }

        return render_template(
            "EmpOrder.html",
            orders=orders,
            stats=stats,
            sessions=sessions,
            staff_name=session.get("username", "Staff"),
            allowed_statuses=["pending", "preparing", "ready"],
        )

    @app.route("/staff/orders/update", methods=["POST"])
    def update_order():
        if (block := require_staff()):
            return block

        # Validate the order ID coming from the form
        try:
            order_id = int(request.form.get("order_id", "").strip())
        except ValueError:
            flash("Choose a valid order before updating.", "warning")
            return redirect("/staff/orders")

        # Validate the status — only these three are allowed
        new_status = (request.form.get("status") or "").strip().lower()
        if new_status not in ("pending", "preparing", "ready"):
            flash("Choose a valid order status.", "warning")
            return redirect("/staff/orders")

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        cursor.execute("SELECT order_id, preparation_time FROM orders WHERE order_id = %s", (order_id,))
        order = cursor.fetchone()

        if not order:
            cursor.close()
            flash("Order not found.", "warning")
            return redirect("/staff/orders")

        original_prep = order["preparation_time"] or 10

        if new_status == "ready":
            cursor.execute("UPDATE orders SET status = 'ready', preparation_time = 0 WHERE order_id = %s", (order_id,))
        elif new_status == "pending":
            cursor.execute("UPDATE orders SET status = 'pending', preparation_time = %s WHERE order_id = %s", (original_prep, order_id))
        else:
            cursor.execute("UPDATE orders SET status = %s WHERE order_id = %s", (new_status, order_id))

        mysql.connection.commit()
        cursor.close()
        flash(f"Order #{order_id} updated to {new_status}.", "success")
        return redirect("/staff/orders")