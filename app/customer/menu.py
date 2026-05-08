from flask import render_template, session, request

def register_menu_routes(app, mysql):

    @app.route("/menu", methods=["GET", "POST"])
    def menu():

        # ✅ read from Flask session instead of URL parameter
        session_id = session.get('table_session_id')

        if not session_id:
            return redirect('/Customer/scan-required')  # ✅ not a 400 error

        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT table_number FROM Table_Session 
            WHERE session_id=%s AND status='active'
        """, (session_id,))
        result = cursor.fetchone()
        cursor.close()

        if not result:
            return redirect('/Customer/scan-required')  # ✅ not a 400 error

        table_number = result[0]

        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT item_id, name, description, preparation_time, price, category
            FROM Item
            ORDER BY category, name
        """)
        items = cursor.fetchall()
        cursor.close()

        return render_template("Menu.html", 
                               session_id=session_id, 
                               table_number=table_number, 
                               items=items)