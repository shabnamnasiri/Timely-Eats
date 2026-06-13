import MySQLdb.cursors
from flask import render_template

from app.admin.helpers import COMPLETED_ORDER_STATUS, admin_required, get_admin_user
from app.staff.orders import get_sessions


def _closed_status_clause():
    return "LOWER(COALESCE(o.status, '')) = %s"


def get_order_report_stats(mysql):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        """
        SELECT
            COUNT(*) AS total_orders,
            COALESCE(AVG(preparation_time), 0) AS avg_prep,
            COALESCE(SUM(total_amount), 0) AS net_revenue
        FROM orders
        WHERE LOWER(COALESCE(status, '')) = %s
        """,
        (COMPLETED_ORDER_STATUS,),
    )
    stats = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) AS total FROM orders")
    all_orders = cursor.fetchone()["total"] or 0
    completed = stats["total_orders"] or 0
    stats["success_rate"] = round((completed / all_orders) * 100) if all_orders else 0

    cursor.close()
    return stats


def get_item_sales(mysql):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        f"""
        SELECT
            i.item_id,
            i.name,
            i.category,
            i.price,
            SUM(od.quantity) AS volume,
            SUM(od.quantity * i.price) AS gross_revenue
        FROM order_details od
        JOIN item i ON i.item_id = od.item_id
        JOIN orders o ON o.order_id = od.order_id
        WHERE {_closed_status_clause()}
        GROUP BY i.item_id, i.name, i.category, i.price
        ORDER BY volume DESC
        """,
        (COMPLETED_ORDER_STATUS,),
    )
    rows = cursor.fetchall()
    cursor.close()
    return rows


def get_revenue_summary(mysql):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        """
        SELECT COALESCE(SUM(total_amount), 0) AS net_sales
        FROM orders
        WHERE LOWER(COALESCE(status, '')) = %s
        """,
        (COMPLETED_ORDER_STATUS,),
    )
    summary = cursor.fetchone()
    cursor.close()

    net_sales = float(summary["net_sales"] or 0)
    tax_rate = 0.06
    tax = round(net_sales * tax_rate, 2)
    return {
        "net_sales": net_sales,
        "tax": tax,
        "discounts": 0.0,
        "refunds": 0.0,
        "gross_total": round(net_sales + tax, 2),
    }


def get_customer_report(mysql):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        """
        SELECT
            u.user_id,
            u.username,
            u.email,
            u.phone_number,
            u.loyalty_point,
            COUNT(o.order_id) AS order_count,
            COALESCE(SUM(o.total_amount), 0) AS total_spend
        FROM user u
        LEFT JOIN orders o
            ON o.user_id = u.user_id
           AND LOWER(COALESCE(o.status, '')) = %s
        WHERE u.role_id = 1
        GROUP BY u.user_id, u.username, u.email, u.phone_number, u.loyalty_point
        ORDER BY total_spend DESC, order_count DESC
        """,
        (COMPLETED_ORDER_STATUS,),
    )
    customers = cursor.fetchall()
    cursor.close()

    total_registered = len(customers)
    active_customers = sum(1 for c in customers if c["order_count"] > 0)
    total_spend = sum(float(c["total_spend"] or 0) for c in customers)
    avg_lifetime = round(total_spend / active_customers, 2) if active_customers else 0

    return customers, {
        "total_registered": total_registered,
        "active_customers": active_customers,
        "active_rate": round((active_customers / total_registered) * 100) if total_registered else 0,
        "avg_lifetime_value": avg_lifetime,
    }


def get_table_report(mysql):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        """
        SELECT COUNT(*) AS total_tables FROM restaurant_table
        """
    )
    table_meta = cursor.fetchone()

    cursor.execute(
        f"""
        SELECT
            ts.table_number,
            COUNT(DISTINCT o.order_id) AS order_count,
            COALESCE(SUM(o.total_amount), 0) AS revenue,
            COALESCE(AVG(o.preparation_time), 0) AS avg_prep,
            (
                SELECT i.category
                FROM order_details od
                JOIN item i ON i.item_id = od.item_id
                JOIN orders o2 ON o2.order_id = od.order_id
                WHERE o2.session_id = ts.session_id
                  AND LOWER(COALESCE(o2.status, '')) = %s
                GROUP BY i.category
                ORDER BY SUM(od.quantity) DESC
                LIMIT 1
            ) AS primary_category
        FROM table_session ts
        LEFT JOIN orders o
            ON o.session_id = ts.session_id
           AND LOWER(COALESCE(o.status, '')) = %s
        GROUP BY ts.table_number
        ORDER BY order_count DESC, ts.table_number ASC
        """,
        (COMPLETED_ORDER_STATUS, COMPLETED_ORDER_STATUS),
    )
    tables = cursor.fetchall()
    cursor.close()

    active_sessions, _ = get_sessions(mysql)
    most_used = tables[0]["table_number"] if tables else "—"
    max_orders = max((t["order_count"] or 0) for t in tables) if tables else 0

    for t in tables:
        count = t["order_count"] or 0
        t["efficiency"] = round((count / max_orders) * 100) if max_orders else 0
        t["primary_category"] = t["primary_category"] or "—"

    return tables, {
        "total_tables": table_meta["total_tables"] or 0,
        "active_tables": len(active_sessions),
        "most_used": most_used,
        "avg_turnover": round(
            sum(t["avg_prep"] or 0 for t in tables) / len(tables)
        ) if tables else 0,
    }


def register_admin_report_routes(app, mysql):

    @app.route("/admin/revenue")
    def admin_revenue():
        guard = admin_required()
        if guard:
            return guard

        summary = get_revenue_summary(mysql)
        items = get_item_sales(mysql)

        return render_template(
            "Revenue.html",
            summary=summary,
            items=items,
            user=get_admin_user(mysql),
        )

    @app.route("/admin/order_report")
    def admin_order_report():
        guard = admin_required()
        if guard:
            return guard

        stats = get_order_report_stats(mysql)
        items = get_item_sales(mysql)

        return render_template(
            "Order_Report.html",
            stats=stats,
            items=items,
            user=get_admin_user(mysql),
        )

    @app.route("/admin/customer_report")
    def admin_customer_report():
        guard = admin_required()
        if guard:
            return guard

        customers, stats = get_customer_report(mysql)

        return render_template(
            "Customer_report.html",
            customers=customers,
            stats=stats,
            user=get_admin_user(mysql),
        )

    @app.route("/admin/table_report")
    def admin_table_report():
        guard = admin_required()
        if guard:
            return guard

        tables, stats = get_table_report(mysql)

        return render_template(
            "Table_report.html",
            tables=tables,
            stats=stats,
            user=get_admin_user(mysql),
        )

    @app.route("/admin/tables")
    def admin_tables():
        guard = admin_required()
        if guard:
            return guard

        sessions, closed_sessions = get_sessions(mysql)

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            """
            SELECT
                rt.table_number,
                rt.qr_status,
                ts.session_id,
                ts.status AS session_status,
                COUNT(o.order_id) AS order_count,
                COALESCE(SUM(o.total_amount), 0) AS running_total
            FROM restaurant_table rt
            LEFT JOIN table_session ts
                ON ts.table_number = rt.table_number
               AND LOWER(COALESCE(ts.status, '')) IN ('active', 'ordered')
            LEFT JOIN orders o ON o.session_id = ts.session_id
            GROUP BY rt.table_number, rt.qr_status, ts.session_id, ts.status
            ORDER BY rt.table_number ASC
            """
        )
        tables = cursor.fetchall()
        cursor.close()

        return render_template(
            "admin_tables.html",
            tables=tables,
            sessions=sessions,
            closed_sessions=closed_sessions,
            user=get_admin_user(mysql),
        )
