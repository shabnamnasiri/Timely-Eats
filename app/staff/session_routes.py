import qrcode
import os
from flask import jsonify, redirect, render_template, request, flash


def register_session_routes(app, mysql):
    # 🔹 PRINT QR PAGE
    @app.route('/staff/print/<int:session_id>')
    def print_qr(session_id):
        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT table_number, qr_code
            FROM Table_Session
            WHERE session_id=%s
        """, (session_id,))

        data = cursor.fetchone()

        if not data:
            return "Invalid session"

        table_number = data[0]

        return render_template(
            'print_qr.html',
            session_id=session_id,
            table_number=table_number,
            qr_code=f"qrcodes/session_{session_id}.png"
        )

    # ==========================================================
    # GET ALL ACTIVE SESSIONS (Excludes closed/inactive rows)
    # ==========================================================
    @app.route('/staff/sessions')
    def get_sessions():
        cursor = mysql.connection.cursor()

        # Added WHERE clause so old closed sessions disappear from your live dashboards
        cursor.execute("""
            SELECT session_id, table_number, status, created_at
            FROM Table_Session
            WHERE LOWER(status) = 'active'
            ORDER BY session_id DESC
        """)

        sessions = cursor.fetchall()

        data = []
        for s in sessions:
            data.append({
                "session_id": s[0],
                "table_number": s[1],
                "status": s[2],
                "created_at": s[3]
            })

        return jsonify(data)

    # =========================
    # QR PAGE
    # =========================
    @app.route('/staff/qr')
    def staff_qr_page():
        return render_template('EmpQR.html')

    # ==========================================================
    # START SESSION (Overwrites previous session to prevent duplicates)
    # ==========================================================
    @app.route('/staff/start-session/<int:table_number>', methods=['POST'])
    def start_session(table_number):
        cursor = mysql.connection.cursor()

        # 🔄 AUTOMATIC OVERWRITE: Deactivate any existing active sessions for this table first
        # This keeps your history safe for analytics but clears it from active views
        cursor.execute("""
            UPDATE Table_Session 
            SET status = 'closed' 
            WHERE table_number = %s AND status = 'active'
        """, (table_number,))
        mysql.connection.commit()

        # 🟢 SAFELY CREATE FRESH NEW ACTIVE SESSION
        cursor.execute("""
            INSERT INTO Table_Session (table_number, status)
            VALUES (%s, 'active')
        """, (table_number,))

        mysql.connection.commit()

        session_id = cursor.lastrowid

        configured_base = app.config.get("PUBLIC_BASE_URL", "")
        if configured_base:
            base_url = configured_base
        else:
            base_url = request.host_url.rstrip("/")

        qr_data = f"{base_url}/session/{session_id}"
        img = qrcode.make(qr_data)

        folder = os.path.join(app.static_folder, "qrcodes")
        os.makedirs(folder, exist_ok=True)

        file_name = f"session_{session_id}.png"
        file_path = os.path.join(folder, file_name)
        img.save(file_path)  # type: ignore
        public_path = f"qrcodes/{file_name}"

        # Save QR path
        cursor.execute("""
            UPDATE Table_Session
            SET qr_code=%s
            WHERE session_id=%s
        """, (public_path, session_id))

        mysql.connection.commit()

        return jsonify({
            "message": "Session started successfully",
            "session_id": session_id,
            "qr_code": public_path
        })

    # =========================
    # CLOSE SESSION
    # =========================
    @app.route('/staff/close-session/<int:session_id>', methods=['POST'])
    def close_session(session_id):
        cursor = mysql.connection.cursor()

        # Double check if any open orders remain unfinished
        cursor.execute("""
            SELECT COUNT(*)
            FROM orders
            WHERE session_id = %s
            AND LOWER(COALESCE(status, '')) NOT IN ('ready')
        """, (session_id,))
        open_order_count = cursor.fetchone()[0]

        if open_order_count:
            cursor.close()
            flash("Finish all orders before closing this session.", "warning")
            return redirect(request.referrer or '/staff/orders')

        # Setting status to 'closed' drops it out of 'active' live feeds instantly
        cursor.execute("UPDATE Table_Session SET status='closed' WHERE session_id=%s", (session_id,))
        mysql.connection.commit()
        cursor.close()

        flash("Session closed successfully.", "success")
        return redirect(request.referrer or '/staff/orders')