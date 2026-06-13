import qrcode
import os
from flask import jsonify, redirect, render_template, request, flash, session
from app.extensions import socketio

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

    # =========================
    # GET ALL SESSIONS
    # =========================
    @app.route('/staff/sessions')
    def get_sessions():
        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT session_id, table_number, status, created_at
            FROM Table_Session
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
        user_id = session.get('user_id')
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT username FROM user WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()

        return render_template("EmpQR.html", staff_name=user)


    # =========================
    # START SESSION (UPDATED)
    # =========================
    @app.route('/staff/start-session/<int:table_number>', methods=['POST'])
    def start_session(table_number):
        cursor = mysql.connection.cursor()

        # 🔴 NEW PART: CHECK IF ACTIVE SESSION EXISTS
        cursor.execute("""
            SELECT * FROM Table_Session
            WHERE table_number=%s AND status='active'
        """, (table_number,))

        existing = cursor.fetchone()

        if existing:
            return jsonify({
                "message": "Table already has an active session"
            }), 400

        # 🟢 CREATE NEW SESSION
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
            "message": "Session started",
            "session_id": session_id,
            "qr_code": public_path
        })
    

    # =========================
    # CLOSE SESSION
    # =========================
    @app.route('/staff/close-session/<int:session_id>', methods=['POST'])
    def close_session(session_id):

        cursor = mysql.connection.cursor()

        # check unfinished orders
        cursor.execute("""
            SELECT COUNT(*)
            FROM orders
            WHERE session_id = %s
            AND LOWER(COALESCE(status, '')) NOT IN ('ready')
        """, (session_id,))

        open_order_count = cursor.fetchone()[0]

        if open_order_count:
            cursor.close()

            flash(
                "Finish all orders before closing this session.",
                "warning"
            )

            return redirect(request.referrer)

        # close session
        cursor.execute("""
            UPDATE Table_Session
            SET status='closed'
            WHERE session_id=%s
        """, (session_id,))

        mysql.connection.commit()
        cursor.close()

        # REAL-TIME notification to customer
        socketio.emit("session_closed", {
            "session_id": session_id
        })

        flash("Session closed successfully.", "success")

        return redirect(request.referrer)