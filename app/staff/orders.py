from datetime import datetime

from flask import flash, redirect, render_template, request, session
import MySQLdb.cursors


ACTIVE_ORDER_STATUSES = {"pending", "pending cash", "preparing", "ready"}
FINAL_ORDER_STATUSES = {"completed", "voided"}
STAFF_ALLOWED_STATUSES = [
    "pending",
    "pending cash",
    "preparing",
    "ready",
    "completed",
    "voided",
]


def _require_staff():
    if "user_id" not in session:
        return redirect("/signin")

    if session.get("role_id") != 2:
        return "Access denied", 403

    return None


def _normalize_status(value):
    return (value or "").strip().lower()


def _build_order_rows(rows):
    orders_by_id = {}

    for row in rows:
        order_id = row["order_id"]

        if order_id not in orders_by_id:
            status = _normalize_status(row["status"])
            payment_method = row["payment_method"] or "unknown"
            payment_status = row["payment_status"] or "pending"
            table_number = row["table_number"]
            order_timestamp = row["timestamp"]
            total_amount = float(row["total_amount"] or 0)
            created_label = order_timestamp.strftime("%Y-%m-%d %H:%M") if order_timestamp else "Unknown"

            orders_by_id[order_id] = {
                "order_id": order_id,
                "session_id": row["session_id"],
                "table_number": table_number,
                "customer_name": row["username"] or f"Customer #{row['user_id']}",
                "status": status,
                "payment_method": payment_method,
                "payment_status": payment_status,
                "total_amount": total_amount,
                "timestamp": order_timestamp,
                "created_label": created_label,
                "items": [],
                "notes": [],
                "item_count": 0,
                "wait_minutes": 0,
                "can_close_session": status in FINAL_ORDER_STATUSES,
                "status_class": status.replace(" ", "-"),
                "payment_label": f"{payment_method.upper()} - {payment_status.title()}",
                "summary": "No items",
            }

        if row["item_name"]:
            quantity = row["quantity"] or 0
            item_name = row["item_name"]
            orders_by_id[order_id]["items"].append(f"{quantity}x {item_name}")
            orders_by_id[order_id]["item_count"] += quantity

        note = (row["customization_note"] or "").strip()
        if note:
            orders_by_id[order_id]["notes"].append(note)

    orders = list(orders_by_id.values())
    orders.sort(
        key=lambda order: (
            order["status"] not in ACTIVE_ORDER_STATUSES,
            -(order["timestamp"].timestamp() if order["timestamp"] else 0),
            -order["order_id"],
        )
    )

    for order in orders:
        order["summary"] = ", ".join(order["items"]) if order["items"] else "No items"

    return orders


def _enrich_order_times(orders):
    for order in orders:
        if order["timestamp"] is None:
            order["wait_minutes"] = 0
            continue

        elapsed_seconds = max((datetime.now() - order["timestamp"]).total_seconds(), 0)
        order["wait_minutes"] = int(elapsed_seconds // 60)


def _load_staff_dashboard(mysql):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        """
        SELECT
            o.order_id,
            o.user_id,
            o.timestamp,
            o.status,
            o.payment_method,
            o.total_amount,
            o.session_id,
            u.username,
            ts.table_number,
            p.payment_status,
            i.name AS item_name,
            od.quantity,
            od.customization_note
        FROM orders o
        LEFT JOIN User u ON u.user_id = o.user_id
        LEFT JOIN Table_Session ts ON ts.session_id = o.session_id
        LEFT JOIN payment p ON p.order_id = o.order_id
        LEFT JOIN order_details od ON od.order_id = o.order_id
        LEFT JOIN item i ON i.item_id = od.item_id
        ORDER BY o.timestamp DESC, od.order_item_id ASC
        """
    )
    order_rows = cursor.fetchall()

    cursor.execute(
        """
        SELECT
            ts.session_id,
            ts.table_number,
            ts.status,
            COUNT(o.order_id) AS order_count,
            SUM(
                CASE
                    WHEN o.order_id IS NULL THEN 0
                    WHEN LOWER(COALESCE(o.status, '')) IN ('completed', 'voided') THEN 0
                    ELSE 1
                END
            ) AS open_order_count
        FROM Table_Session ts
        LEFT JOIN orders o ON o.session_id = ts.session_id
        GROUP BY ts.session_id, ts.table_number, ts.status
        ORDER BY ts.status = 'active' DESC, ts.created_at DESC, ts.session_id DESC
        """
    )
    session_rows = cursor.fetchall()
    cursor.close()

    orders = _build_order_rows(order_rows)
    _enrich_order_times(orders)

    stats = {
        "active_orders": sum(1 for order in orders if order["status"] in ACTIVE_ORDER_STATUSES),
        "pending_orders": sum(1 for order in orders if order["status"] in {"pending", "pending cash"}),
        "preparing_orders": sum(1 for order in orders if order["status"] == "preparing"),
        "ready_orders": sum(1 for order in orders if order["status"] == "ready"),
        "completed_orders": sum(1 for order in orders if order["status"] == "completed"),
        "avg_wait_minutes": int(sum(order["wait_minutes"] for order in orders) / len(orders)) if orders else 0,
        "revenue": sum(order["total_amount"] for order in orders if order["status"] != "voided"),
    }

    sessions = []
    session_close_map = {}
    for session_row in session_rows:
        session_status = _normalize_status(session_row["status"])
        open_order_count = int(session_row["open_order_count"] or 0)
        can_close = session_status == "active" and open_order_count == 0
        sessions.append(
            {
                "session_id": session_row["session_id"],
                "table_number": session_row["table_number"],
                "status": session_status,
                "order_count": int(session_row["order_count"] or 0),
                "open_order_count": open_order_count,
                "can_close": can_close,
            }
        )
        session_close_map[session_row["session_id"]] = can_close

    for order in orders:
        if order["session_id"] in session_close_map:
            order["can_close_session"] = session_close_map[order["session_id"]]

    return orders, stats, sessions


def register_staff_order_routes(app, mysql):

    @app.route("/staff/orders")
    def staff_orders():
        auth_redirect = _require_staff()
        if auth_redirect:
            return auth_redirect

        orders, stats, sessions = _load_staff_dashboard(mysql)
        return render_template(
            "EmpOrder.html",
            orders=orders,
            stats=stats,
            sessions=sessions,
            staff_name=session.get("username", "Staff"),
            allowed_statuses=STAFF_ALLOWED_STATUSES,
        )

    @app.route("/staff/orders/update", methods=["POST"])
    def update_staff_order():
        auth_redirect = _require_staff()
        if auth_redirect:
            return auth_redirect

        try:
            order_id = int(request.form.get("order_id", "").strip())
        except ValueError:
            flash("Choose a valid order before updating.", "warning")
            return redirect("/staff/orders")

        new_status = _normalize_status(request.form.get("status"))
        if new_status not in STAFF_ALLOWED_STATUSES:
            flash("Choose a valid order status.", "warning")
            return redirect("/staff/orders")

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            """
            SELECT order_id, session_id
            FROM orders
            WHERE order_id = %s
            """,
            (order_id,),
        )
        order = cursor.fetchone()

        if not order:
            cursor.close()
            flash("Order not found.", "warning")
            return redirect("/staff/orders")

        cursor.execute(
            """
            UPDATE orders
            SET status = %s
            WHERE order_id = %s
            """,
            (new_status, order_id),
        )

        if new_status == "completed":
            cursor.execute(
                """
                UPDATE payment
                SET payment_status = CASE
                    WHEN LOWER(COALESCE(payment_status, '')) = 'pending' THEN 'confirmed'
                    ELSE payment_status
                END
                WHERE order_id = %s
                """,
                (order_id,),
            )
        elif new_status == "voided":
            cursor.execute(
                """
                UPDATE payment
                SET payment_status = 'voided'
                WHERE order_id = %s
                """,
                (order_id,),
            )

        mysql.connection.commit()
        cursor.close()
        flash(f"Order #{order_id} updated to {new_status}.", "success")
        return redirect("/staff/orders")

    @app.route("/staff/sessions/<int:session_id>/close", methods=["POST"])
    def close_staff_session(session_id):
        auth_redirect = _require_staff()
        if auth_redirect:
            return auth_redirect

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            """
            SELECT session_id, table_number, status
            FROM Table_Session
            WHERE session_id = %s
            """,
            (session_id,),
        )
        table_session = cursor.fetchone()

        if not table_session:
            cursor.close()
            flash("Session not found.", "warning")
            return redirect("/staff/orders")

        if _normalize_status(table_session["status"]) != "active":
            cursor.close()
            flash("This session is already closed.", "warning")
            return redirect("/staff/orders")

        cursor.execute(
            """
            SELECT COUNT(*) AS open_order_count
            FROM orders
            WHERE session_id = %s
              AND LOWER(COALESCE(status, '')) NOT IN ('completed', 'voided')
            """,
            (session_id,),
        )
        open_orders = cursor.fetchone()["open_order_count"]

        if open_orders:
            cursor.close()
            flash("Finish or void all orders for this table before closing the session.", "warning")
            return redirect("/staff/orders")

        cursor.execute(
            """
            UPDATE Table_Session
            SET status = 'closed'
            WHERE session_id = %s
            """,
            (session_id,),
        )
        mysql.connection.commit()
        cursor.close()

        flash(
            f"Table {table_session['table_number']} session closed successfully.",
            "success",
        )
        return redirect("/staff/orders")
