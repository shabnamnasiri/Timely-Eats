from flask import render_template, session, redirect, url_for, flash


def register_order_history_routes(app, mysql):
    @app.route('/customer/order_history')
    def order_history():
        # 1. Identity Verification
        if not session.get('user_id'):
            flash("Please sign in to view your order history.", "danger")
            return redirect(url_for('signin'))

        user_id = session['user_id']
        cursor = mysql.connection.cursor()

        # 2. Executing relational data aggregation query.
        # Uses INNER JOIN to omit broken or empty test orders.
        cursor.execute("""
            SELECT 
                o.order_id, 
                o.timestamp, 
                o.total_amount, 
                o.status,
                GROUP_CONCAT(CONCAT(od.quantity, 'x ', i.name) SEPARATOR ', ') AS items_summary
            FROM `orders` o
            INNER JOIN order_details od ON o.order_id = od.order_id
            INNER JOIN item i ON od.item_id = i.item_id
            WHERE o.user_id = %s
            GROUP BY o.order_id
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
            order_id = row[0]
            # Safely format timestamp from database schema
            order_date = row[1].strftime('%b %d, %Y # %I:%M %p') if row[1] else "N/A"
            total_amount = float(row[2]) if row[2] else 0.0
            status = row[3].lower() if row[3] else "unknown"
            items_text_summary = row[4] or "No items listed"

            order_data = {
                "id": order_id,
                "date": order_date,
                "total": total_amount,
                "status": status,
                "summary": items_text_summary  # Mapped safely to avoid native dictionary .items() conflict
            }

            # Accumulate financial total tracking metrics for completed orders only
            if status == 'completed':
                total_spent += total_amount

            # Distribute into active or background log arrays
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