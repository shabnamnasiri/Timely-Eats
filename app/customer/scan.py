from flask import redirect, session, request


def register_scan_routes(app, mysql):

    @app.route('/session/<int:session_id>')
    def scan_qr(session_id):

        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT session_id FROM table_session
            WHERE session_id = %s AND status = 'active'
        """, (session_id,))
        table_session = cursor.fetchone()
        cursor.close()

        if not table_session:
            return "This QR is no longer valid", 403

        # ✅ Save session_id
        session['table_session_id'] = session_id

        # If already logged in
        if session.get('user_id'):
            if session.get('role_id') == 1:  # ✅ only customers
                return redirect('/menu')
            else:
                return "Access denied. This QR is for customers only.", 403

        return redirect('/signin')

