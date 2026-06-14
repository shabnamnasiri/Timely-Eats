from flask import render_template, redirect, session, flash, request
from werkzeug.security import check_password_hash, generate_password_hash
import MySQLdb.cursors


def register_customer_profile_routes(app, mysql):

    # ---------------- PROFILE PAGE ----------------
    @app.route('/customer/profile')
    def customer_profile():
        user_id = session.get('user_id')
        if not user_id:
            return redirect('/signin')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT username, email, phone_number, loyalty_point
            FROM user WHERE user_id = %s
        """, (user_id,))
        user_data = cursor.fetchone()
        cursor.close()

        return render_template('profile.html', user=user_data)


    # ---------------- UPDATE INFO ----------------
    @app.route('/customer/profile/update-info', methods=['POST'])
    def customer_profile_update_info():
        user_id = session.get('user_id')
        if not user_id:
            return redirect('/signin')

        username = request.form.get('username', '').strip()
        phone_number = request.form.get('phone_number', '').strip()

        if not username:
            flash('Username cannot be empty.', 'error')
            return redirect('/customer/profile')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Check if username is taken by another user
        cursor.execute("""
            SELECT user_id FROM user WHERE username = %s AND user_id != %s
        """, (username, user_id))
        if cursor.fetchone():
            cursor.close()
            flash('That username is already taken.', 'error')
            return redirect('/customer/profile')

        cursor.execute("""
            UPDATE user SET username = %s, phone_number = %s WHERE user_id = %s
        """, (username, phone_number or None, user_id))
        mysql.connection.commit()
        cursor.close()

        session['username'] = username
        flash('Profile updated successfully.', 'success')
        return redirect('/customer/profile')


    # ---------------- UPDATE PASSWORD ----------------
    @app.route('/customer/profile/update-password', methods=['POST'])
    def customer_profile_update_password():
        user_id = session.get('user_id')
        if not user_id:
            return redirect('/signin')

        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not current_password or not new_password or not confirm_password:
            flash('All password fields are required.', 'error')
            return redirect('/customer/profile')

        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return redirect('/customer/profile')

        if len(new_password) < 8:
            flash('New password must be at least 8 characters.', 'error')
            return redirect('/customer/profile')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT password FROM user WHERE user_id = %s
        """, (user_id,))
        user = cursor.fetchone()

        if not user or not check_password_hash(user['password'], current_password):
            cursor.close()
            flash('Current password is incorrect.', 'error')
            return redirect('/customer/profile')

        hashed = generate_password_hash(new_password)
        cursor.execute("""
            UPDATE user SET password = %s WHERE user_id = %s
        """, (hashed, user_id))
        mysql.connection.commit()
        cursor.close()

        flash('Password updated successfully.', 'success')
        return redirect('/customer/profile')