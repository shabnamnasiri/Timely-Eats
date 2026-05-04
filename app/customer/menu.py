from flask import render_template, session, request

def register_menu_routes(app, mysql):

    @app.route("/menu", methods=["GET", "POST"])
    def menu():

        session_id = request.args.get("session_id") or session.get("table_session_id")
        table_number = None

        if not session_id:
            return "No session provided", 400

        session["table_session_id"] = str(session_id)

        cursor = mysql.connection.cursor()

        # Get table number from session
        cursor.execute("""
            SELECT table_number FROM Table_Session 
            WHERE session_id=%s AND status='active'
        """, (session_id,))
        result = cursor.fetchone()

        if not result:
            return "Invalid or expired session", 400

        table_number = result[0]

        # Get menu items
        cursor.execute("""
            SELECT item_id, name, description, preparation_time, price, category
            FROM Item
            ORDER BY category, name
        """)
        items = cursor.fetchall()
        cursor.close()

        return render_template("Menu.html", session_id=session_id, table_number=table_number, items=items)
