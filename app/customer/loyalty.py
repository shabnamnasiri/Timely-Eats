from flask import render_template, session, redirect, url_for, flash
import MySQLdb.cursors

def register_loyalty_routes(app, mysql):
    @app.route('/customer/loyalty')
    def loyalty_dashboard():
        user_id = session.get('user_id')
        if not user_id:
            flash("Please sign in to view your rewards.", "danger")
            return redirect(url_for('signin'))

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # 1. Fetch current user point balances
        cursor.execute("SELECT loyalty_point FROM User WHERE user_id = %s", (user_id,))
        user_data = cursor.fetchone()
        current_points = user_data['loyalty_point'] if user_data else 0

        # Progress logic toward next 100-point reward milestone
        points_to_next_reward = 100 - (current_points % 100)
        if points_to_next_reward == 0 and current_points > 0:
            points_to_next_reward = 100
        progress_percentage = (current_points % 100)

        # 2. Fetch Active/Available Coupons (✅ ESCAPED DATE_FORMAT PERCENTAGES)
        cursor.execute("""
            SELECT code, discount_amount, DATE_FORMAT(created_at, '%%b %%d, %%Y') as date_created 
            FROM coupons 
            WHERE user_id = %s AND status = 'available'
            ORDER BY created_at DESC
        """, (user_id,))
        available_coupons = cursor.fetchall()

        # 3. Fetch Used/Historical Coupons (✅ ESCAPED DATE_FORMAT PERCENTAGES)
        cursor.execute("""
            SELECT c.code, c.discount_amount, DATE_FORMAT(c.used_at, '%%b %%d, %%Y') as date_used, c.order_id
            FROM coupons c
            WHERE c.user_id = %s AND c.status = 'used'
            ORDER BY c.used_at DESC
        """, (user_id,))
        used_coupons = cursor.fetchall()

        # 4. Fetch Point Transaction History Ledger (✅ ESCAPED DATE_FORMAT PERCENTAGES)
        cursor.execute("""
            SELECT points_changed, transaction_type, description, DATE_FORMAT(timestamp, '%%b %%d, %%Y # %%I:%%M %%p') as date_logged
            FROM loyalty_history
            WHERE user_id = %s
            ORDER BY timestamp DESC
        """, (user_id,))
        points_ledger = cursor.fetchall()

        cursor.close()

        return render_template(
            "loyalty.html",
            current_points=current_points,
            points_to_next_reward=points_to_next_reward,
            progress_percentage=progress_percentage,
            available_coupons=available_coupons,
            used_coupons=used_coupons,
            points_ledger=points_ledger
        )