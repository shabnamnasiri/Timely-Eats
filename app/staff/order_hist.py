from flask import render_template, session, redirect, flash
import MySQLdb.cursors


def require_staff():
    if "user_id" not in session or session.get("role_id") != 2:
        return "Access denied", 403
    return None


def register_staff_order_history_routes(app, mysql):
    @app.route("/staff/order_hist")
    def staff_order_history():
        if (block := require_staff()):
            return block

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Pull closed workspaces with aggregated orders, prices, and buyer usernames
        cursor.execute("""
            SELECT 
                ts.session_id,
                ts.table_number,
                ts.created_at,
                o.order_id,
                o.status AS order_status,
                o.total_amount,
                COALESCE(u.username, CONCAT('Customer #', o.user_id)) AS customer_name,
                GROUP_CONCAT(CONCAT(od.quantity, 'x ', i.name) SEPARATOR ', ') AS ticket_summary
            FROM Table_Session ts
            INNER JOIN orders o ON o.session_id = ts.session_id
            LEFT JOIN User u ON u.user_id = o.user_id
            LEFT JOIN order_details od ON od.order_id = o.order_id
            LEFT JOIN item i ON od.item_id = i.item_id
            WHERE LOWER(COALESCE(ts.status, '')) = 'closed'
            GROUP BY ts.session_id, ts.table_number, ts.created_at, o.order_id, o.status, o.total_amount, u.username
            ORDER BY ts.created_at DESC, o.order_id DESC
        """)
        rows = cursor.fetchall()
        cursor.close()

        # Group individual backend rows into a nested, session-first tree hierarchy
        sessions_map = {}
        for row in rows:
            sid = row["session_id"]
            if sid not in sessions_map:
                sessions_map[sid] = {
                    "session_id": sid,
                    "table_number": row["table_number"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else "",
                    "formatted_date": row["created_at"].strftime("%b %d, %Y # %I:%M %p") if row[
                        "created_at"] else "N/A",
                    "total_session_bill": 0.0,
                    "associated_customers": set(),
                    "orders": []
                }

            sessions_map[sid]["associated_customers"].add(row["customer_name"])
            sessions_map[sid]["total_session_bill"] += float(row["total_amount"] or 0.0)

            sessions_map[sid]["orders"].append({
                "order_id": row["order_id"],
                "status": (row["order_status"] or "completed").lower(),
                "customer": row["customer_name"],
                "amount": float(row["total_amount"] or 0.0),
                "summary": row["ticket_summary"] or "No items"
            })

        # Final serialization adjustment for template transmission
        history_sessions = list(sessions_map.values())
        for s in history_sessions:
            s["customer_list_string"] = ", ".join(s["associated_customers"])

        return render_template(
            "EmpHistory.html",
            sessions=history_sessions,
            staff_name=session.get("username", "Staff")
        )