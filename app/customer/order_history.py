from flask import render_template, session, redirect, url_for, flash
import MySQLdb.cursors


def register_order_history_routes(app, mysql):
    @app.route('/customer/order_history')
    def order_history():
        # 1. Identity Verification
        if not session.get('user_id'):
            flash("Please sign in to view your order history.", "danger")
            return redirect(url_for('signin'))

        user_id = session['user_id']

        # Using DictCursor to keep object key mutations clean and expressive
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # 2. Executing relational data aggregation query.
        # Added ts.status to verify if the physical workspace is still live
        cursor.execute("""
            SELECT 
                o.order_id, 
                o.timestamp, 
                o.total_amount, 
                o.status,
                LOWER(COALESCE(ts.status, '')) AS session_status,
                GROUP_CONCAT(CONCAT(od.quantity, 'x ', i.name) SEPARATOR ', ') AS items_summary
            FROM `orders` o
            INNER JOIN order_details od ON o.order_id = od.order_id
            INNER JOIN item i ON od.item_id = i.item_id
            LEFT JOIN Table_Session ts ON o.session_id = ts.session_id
            WHERE o.user_id = %s
            GROUP BY o.order_id, o.timestamp, o.total_amount, o.status, ts.status
            ORDER BY o.timestamp DESC
        """, (user_id,))

        all_orders = cursor.fetchall()
        cursor.close()

        # 3. Initializing data buckets
        active_orders = []
        past_orders = []
        total_spent = 0.0

        # Current preparation statuses inside the kitchen pipeline
        ongoing_statuses = ['pending', 'preparing', 'cooking', 'ready']

        # 4. Sorting data rows into matching frontend dict models
        for row in all_orders:
            order_id = row["order_id"]
            order_date = row["timestamp"].strftime('%b %d, %Y # %I:%M %p') if row["timestamp"] else "N/A"
            total_amount = float(row["total_amount"]) if row["total_amount"] else 0.0
            status = row["status"].lower() if row["status"] else "unknown"
            session_status = row["session_status"]
            items_text_summary = row["items_summary"] or "No items listed"

            # 🔴 FIX STEP: If an order is 'ready' but the table session was terminated,
            # force it to behave as 'completed' so it falls out of active views.
            if status == 'ready' and session_status == 'closed':
                status = 'completed'

            order_data = {
                "id": order_id,
                "date": order_date,
                "total": total_amount,
                "status": status,
                "summary": items_text_summary
            }

            # Accumulate financial total tracking metrics for completed orders only
            if status == 'completed':
                total_spent += total_amount

            # Distribute into active or background historical log arrays
            if status in ongoing_statuses:
                active_orders.append(order_data)
            else:
                past_orders.append(order_data)

        # 5. Render view interface template layer
        return render_template(
            "Order_History.html",
            active_orders=active_orders,
            past_orders=past_orders,
            total_spent=round(total_spent, 2)
        )