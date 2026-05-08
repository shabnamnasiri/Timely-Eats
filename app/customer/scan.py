from flask import redirect, session, flash,render_template


def register_scan_routes(app, mysql):

    @app.route('/session/<int:session_id>')
    def scan_qr(session_id):

        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT session_id, table_number FROM Table_Session
            WHERE session_id = %s AND status = 'active'
        """, (session_id,))
        result = cursor.fetchone()
        cursor.close()

        if not result:
            session.clear()
            flash("This QR code is no longer valid. Please ask staff for assistance.", "danger")
            return redirect('/signin')

        # ✅ Save table info
        session['table_session_id'] = result[0]
        session['table_number'] = result[1]
        session.modified = True

        # ✅ Already logged in — verify user exists in DB
        if session.get('user_id'):
            cursor = mysql.connection.cursor()
            cursor.execute("""
                SELECT user_id, role_id FROM User WHERE user_id = %s
            """, (session['user_id'],))
            user = cursor.fetchone()
            cursor.close()

            if not user:
                session.clear()
                session['table_session_id'] = result[0]
                session['table_number'] = result[1]
                flash(f"Welcome to Table {result[1]}! Please sign in to continue.", "success")
                return redirect('/signin')

            if user[1] == 1:  # customer
                flash(f"Welcome back! You're at Table {result[1]}.", "success")
                return redirect('/menu')
            else:
                session.clear()
                flash("This QR is for customers only. You have been logged out.", "danger")
                return redirect('/signin')

        # ✅ Not logged in
        flash(f"Welcome to Table {result[1]}! Please sign in to continue.", "success")
        return redirect('/signin')
    @app.route('/Customer/scan-required')
    def scan_required():
        return render_template('ScanRequired.html')