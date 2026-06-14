from flask import render_template, redirect, session, flash


def register_admin_analytics_routes(app, mysql):

    def admin_required():
        if "user_id" not in session:
            flash("Please sign in to access this page.", "warning")
            return redirect("/signin")
        if session.get("role_id") != 3:
            flash("Access denied. Admins only.", "danger")
            return redirect("/signin")
        return None

    # ──────────────────────────────────────────────
    # REVENUE REPORT
    # ──────────────────────────────────────────────
    @app.route("/admin/revenue")
    def admin_revenue():
        guard = admin_required()
        if guard:
            return guard

        cursor = mysql.connection.cursor()

        # Per-item sales: units sold, avg price, total revenue
        cursor.execute("""
            SELECT
                i.name                          AS item_name,
                i.category                      AS category,
                SUM(od.quantity)                AS units_sold,
                i.price                         AS avg_price,
                SUM(od.quantity * i.price)      AS total_revenue
            FROM order_details od
            JOIN item i ON od.item_id = i.item_id
            JOIN orders o ON od.order_id = o.order_id
            GROUP BY i.item_id, i.name, i.category, i.price
            ORDER BY total_revenue DESC
        """)
        items = cursor.fetchall()

        # Summary stats
        cursor.execute("""
            SELECT
                COALESCE(SUM(od.quantity * i.price), 0) AS net_sales
            FROM order_details od
            JOIN item i ON od.item_id = i.item_id
            JOIN orders o ON od.order_id = o.order_id
        """)
        row = cursor.fetchone()
        net_sales = float(row[0]) if row else 0.0
        tax       = round(net_sales * 0.06, 2)
        gross     = round(net_sales + tax, 2)

        cursor.close()

        return render_template(
            "Revenue.html",
            items=items,
            net_sales=net_sales,
            tax=tax,
            gross=gross,
        )

    # ──────────────────────────────────────────────
    # ORDER REPORT  (popular items / daily count)
    # ──────────────────────────────────────────────
    @app.route("/admin/order_report")
    def admin_order_report():
        guard = admin_required()
        if guard:
            return guard

        cursor = mysql.connection.cursor()

        # Popular items ranked by volume
        cursor.execute("""
            SELECT
                i.name                          AS item_name,
                SUM(od.quantity)                AS volume,
                SUM(od.quantity * i.price)      AS gross_rev
            FROM order_details od
            JOIN item i ON od.item_id = i.item_id
            JOIN orders o ON od.order_id = o.order_id
            GROUP BY i.item_id, i.name
            ORDER BY volume DESC
        """)
        popular_items = cursor.fetchall()

        # Summary stats
        cursor.execute("SELECT COUNT(*) FROM orders")
        total_orders = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT COALESCE(SUM(od.quantity * i.price), 0)
            FROM order_details od
            JOIN item i ON od.item_id = i.item_id
        """)
        net_revenue = float(cursor.fetchone()[0] or 0)

        # Daily order count for the last 7 days
        cursor.execute("""
            SELECT
                DATE(created_at)    AS order_date,
                COUNT(*)            AS daily_count
            FROM orders
            WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
            GROUP BY DATE(created_at)
            ORDER BY order_date ASC
        """)
        daily_counts = cursor.fetchall()

        cursor.close()

        return render_template(
            "Order_Report.html",
            popular_items=popular_items,
            total_orders=total_orders,
            net_revenue=net_revenue,
            daily_counts=daily_counts,
        )

    # ──────────────────────────────────────────────
    # CUSTOMER REPORT
    # ──────────────────────────────────────────────
    @app.route("/admin/customer_report")
    def admin_customer_report():
        guard = admin_required()
        if guard:
            return guard

        cursor = mysql.connection.cursor()

        # Per-customer spend + order count
        cursor.execute("""
            SELECT
                u.user_id,
                u.username,
                u.email,
                u.created_at                            AS joined_date,
                COUNT(DISTINCT o.order_id)              AS total_orders,
                COALESCE(SUM(od.quantity * i.price), 0) AS total_spend
            FROM user u
            LEFT JOIN orders o  ON o.user_id = u.user_id
            LEFT JOIN order_details od ON od.order_id = o.order_id
            LEFT JOIN item i    ON i.item_id = od.item_id
            WHERE u.role_id = 1
            GROUP BY u.user_id, u.username, u.email, u.created_at
            ORDER BY total_spend DESC
        """)
        customers = cursor.fetchall()

        # Summary stats
        cursor.execute("SELECT COUNT(*) FROM user WHERE role_id = 1")
        total_registered = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT COUNT(*) FROM user
            WHERE role_id = 1
              AND MONTH(created_at) = MONTH(CURDATE())
              AND YEAR(created_at)  = YEAR(CURDATE())
        """)
        new_this_month = cursor.fetchone()[0] or 0

        avg_ltv = 0
        if customers:
            avg_ltv = round(
                sum(float(c[5]) for c in customers) / len(customers), 2
            )

        cursor.close()

        return render_template(
            "Customer_report.html",
            customers=customers,
            total_registered=total_registered,
            new_this_month=new_this_month,
            avg_ltv=avg_ltv,
        )

    # ──────────────────────────────────────────────
    # TABLE REPORT
    # ──────────────────────────────────────────────
    @app.route("/admin/table_report")
    def admin_table_report():
        guard = admin_required()
        if guard:
            return guard

        cursor = mysql.connection.cursor()

        # Per-table: order count, avg session duration, top category ordered
        cursor.execute("""
            SELECT
                rt.table_id,
                rt.table_number,
                COUNT(DISTINCT o.order_id)                              AS order_count,
                COALESCE(
                    ROUND(
                        AVG(
                            TIMESTAMPDIFF(MINUTE, ts.started_at, ts.ended_at)
                        ), 0
                    ), 0
                )                                                       AS avg_minutes,
                (
                    SELECT i2.category
                    FROM order_details od2
                    JOIN item i2 ON i2.item_id = od2.item_id
                    JOIN orders o2 ON o2.order_id = od2.order_id
                    JOIN table_session ts2 ON ts2.session_id = o2.session_id
                    WHERE ts2.table_id = rt.table_id
                    GROUP BY i2.category
                    ORDER BY SUM(od2.quantity) DESC
                    LIMIT 1
                )                                                       AS top_category
            FROM restaurant_table rt
            LEFT JOIN table_session ts ON ts.table_id = rt.table_id
            LEFT JOIN orders o ON o.session_id = ts.session_id
            GROUP BY rt.table_id, rt.table_number
            ORDER BY order_count DESC
        """)
        tables = cursor.fetchall()

        # Summary stats
        cursor.execute("SELECT COUNT(*) FROM restaurant_table")
        total_tables = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT COUNT(DISTINCT table_id)
            FROM table_session
            WHERE ended_at IS NULL
        """)
        active_tables = cursor.fetchone()[0] or 0

        # Most-used table number
        most_used = tables[0][1] if tables else "—"

        # Overall avg turnover (minutes)
        cursor.execute("""
            SELECT ROUND(AVG(TIMESTAMPDIFF(MINUTE, started_at, ended_at)), 0)
            FROM table_session
            WHERE ended_at IS NOT NULL
        """)
        avg_turnover = cursor.fetchone()[0] or 0

        # Max orders across tables (for efficiency bar width)
        max_orders = tables[0][2] if tables else 1

        cursor.close()

        return render_template(
            "Table_report.html",
            tables=tables,
            total_tables=total_tables,
            active_tables=active_tables,
            most_used=most_used,
            avg_turnover=avg_turnover,
            max_orders=max_orders if max_orders > 0 else 1,
        )