from flask import redirect, session, flash, render_template


def register_scan_routes(app, mysql):

    @app.route('/session/<int:session_id>')
    def scan_qr(session_id):

        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT session_id, table_number, status FROM Table_Session
            WHERE session_id = %s AND status IN ('active', 'ordered')
        """, (session_id,))
        result = cursor.fetchone()

        if not result:
            cursor.close()
            session.clear()
            flash("This QR code is no longer valid. Please ask staff for assistance.", "danger")
            return redirect('/signin')

        ts_id     = result[0]
        table_num = result[1]
        ts_status = result[2]

        if ts_status == 'ordered':
            cursor.execute("""
                SELECT DISTINCT user_id FROM orders
                WHERE session_id = %s AND status IN ('pending', 'ordered')
                LIMIT 1
            """, (ts_id,))
            owner = cursor.fetchone()
            cursor.close()

            if owner:
                owner_id = owner[0]
                session['table_session_id'] = ts_id
                session['table_number'] = table_num
                session.modified = True

                if session.get('user_id') == owner_id:
                    # Same user already logged in
                    flash(f"Welcome back! You're at Table {table_num}.", "success")
                    return redirect('/menu')
                else:
                    # Need to verify identity at login
                    session['expected_user_id'] = owner_id
                    flash(f"Welcome back to Table {table_num}! Please sign in to continue.", "success")
                    return redirect('/signin')
            # No orders found — fall through to active flow

        else:
            cursor.close()

        # Active session flow
        session['table_session_id'] = ts_id
        session['table_number'] = table_num
        session.pop('expected_user_id', None)
        session.modified = True

        if session.get('user_id'):
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT user_id, role_id FROM User WHERE user_id = %s", (session['user_id'],))
            user = cursor.fetchone()
            cursor.close()

            if not user:
                session.clear()
                session['table_session_id'] = ts_id
                session['table_number'] = table_num
                flash(f"Welcome to Table {table_num}! Please sign in to continue.", "success")
                return redirect('/signin')

            if user[1] == 1:
                flash(f"Welcome back! You're at Table {table_num}.", "success")
                return redirect('/menu')
            else:
                session.clear()
                flash("This QR is for customers only. You have been logged out.", "danger")
                return redirect('/signin')

        flash(f"Welcome to Table {table_num}! Please sign in to continue.", "success")
        return redirect('/signin')

    @app.route('/Customer/scan-required')
    def scan_required():
        return render_template('ScanRequired.html')