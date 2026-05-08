from flask import redirect, session, request


def register_scan_routes(app, mysql):

    @app.route('/session/<int:session_id>')
    def scan_qr(session_id):

        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT status FROM Table_Session
            WHERE session_id = %s
        """, (session_id,))          # ✅ Table_Session not table_session
        result = cursor.fetchone()
        cursor.close()

        if not result:
            return "Invalid QR", 403

        if result[0] != 'active':
            return "This QR is no longer valid", 403

        # ✅ Save to Flask session
        session['table_session_id'] = session_id
        session.modified = True

        if session.get('user_id'):
            if session.get('role_id') == 1:
                return redirect('/menu')
            else:
                return "Access denied. This QR is for customers only.", 403

        return redirect('/signin')

    @app.route('/scan-required')
    def scan_required():
        return "Please scan the QR code on your table to continue.", 403