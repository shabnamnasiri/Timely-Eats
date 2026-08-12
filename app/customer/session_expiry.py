from datetime import datetime, timedelta
from flask import session as flask_session
from flask_socketio import join_room


def register_session_expiry_task(app, mysql, socketio):
    """
    Background task: every 60 seconds, close any table_session where
    updated_at (or created_at if never updated) is >= 20 minutes ago
    and status is still 'active' or 'ordered'.
    Emits 'session_closed' to the affected session room so the customer
    gets redirected immediately.
    """

    def check_expired_sessions():
        # Loop forever, checking every 60 seconds.
        while True:
            socketio.sleep(60)
            try:
                # Needed so we can use the database outside a normal request.
                with app.app_context():
                    conn = mysql.connection
                    cursor = conn.cursor()

                    now = datetime.now()
                    cutoff = now - timedelta(minutes=20)

                    # Find sessions that haven't been touched in 20+ minutes.
                    cursor.execute("""
                        SELECT session_id
                        FROM table_session
                        WHERE status IN ('active', 'ordered')
                          AND COALESCE(updated_at, created_at) <= %s
                    """, (cutoff,))
                    expired = cursor.fetchall()

                    if expired:
                        for row in expired:
                            sid = row[0]

                            # Close the session in the database.
                            cursor.execute("""
                                UPDATE table_session
                                SET status = 'closed', closed_at = %s
                                WHERE session_id = %s
                            """, (now, sid))

                            # Tell the customer's browser the session expired.
                            socketio.emit(
                                'session_closed',
                                {'message': 'Your table session has expired.'},
                                room=f'table_session_{sid}'
                            )
                            print(f"[SESSION EXPIRY] Closed session {sid}")

                        conn.commit()

                    cursor.close()

            except Exception as e:
                # Don't crash the loop, just log and try again next time.
                print(f"[SESSION EXPIRY ERROR] {e}")

    # Start the loop above as a background task.
    socketio.start_background_task(check_expired_sessions)


def register_session_room_events(socketio):
    """
    Let customers join their table session room so they receive
    session_closed events.
    """

    @socketio.on('join_session_room')
    def join_session_room(data):
        # The customer's browser sends this when it connects, so it can
        # later receive the 'session_closed' message above.
        session_id = data.get('session_id')
        if session_id:
            join_room(f'table_session_{session_id}')
            print(f"[SOCKET] Client joined table_session_{session_id}")