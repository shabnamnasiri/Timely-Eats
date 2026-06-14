from flask import render_template, redirect, session
import MySQLdb.cursors


def register_customer_order_history_routes(app, mysql):

    @app.route('/customer/order_history')
    def customer_order_history():
        user_id = session.get('user_id')
        if not user_id:
            return redirect('/signin')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT
                o.order_id,
                o.timestamp,
                o.total_amount,
                o.status,
                GROUP_CONCAT(CONCAT(i.name, ' x', od.quantity) SEPARATOR ', ') AS summary
            FROM orders o
            LEFT JOIN order_details od ON o.order_id = od.order_id
            LEFT JOIN item i ON od.item_id = i.item_id
            WHERE o.user_id = %s
            GROUP BY o.order_id
            ORDER BY o.timestamp DESC
        """, (user_id,))
        rows = cursor.fetchall()
        cursor.close()

        active_statuses = {'pending', 'preparing'}
        past_statuses   = {'completed', 'cancelled', 'ready'}

        active_orders = []
        past_orders   = []
        total_spent   = 0.0

        for row in rows:
            status = row['status']

            # Treat ready as completed for display/filter purposes
            display_status = 'completed' if status == 'ready' else status

            order = {
                'id':      row['order_id'],
                'status':  display_status,
                'summary': row['summary'] or '',
                'date':    row['timestamp'].strftime('%b %d, %Y  %H:%M') if row['timestamp'] else '—',
                'total':   float(row['total_amount'] or 0),
            }

            if status in active_statuses:
                active_orders.append(order)
            elif status in past_statuses:
                past_orders.append(order)
                # Count ready and completed both toward total spent
                if status in {'completed', 'ready'}:
                    total_spent += order['total']

        return render_template(
            'order_history.html',
            active_orders=active_orders,
            past_orders=past_orders,
            total_spent=total_spent,
        )