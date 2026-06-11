from flask import render_template, session, request,redirect

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
        WHERE session_id=%s AND status IN ('active', 'ordered')
    """, (session_id,))
        result = cursor.fetchone()
        cursor.close()

        if not result:
            return redirect('/Customer/scan-required')  # ✅ not a 400 error

        table_number = result[0]

        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT 
                i.item_id,
                i.name,
                i.description,
                i.preparation_time,
                i.price,
                i.category,
                COALESCE(ROUND(AVG(r.rating), 0), 0) AS avg_rating
            FROM Item i
            LEFT JOIN Review r ON i.item_id = r.item_id
            GROUP BY 
                i.item_id, i.name, i.description, 
                i.preparation_time, i.price, i.category
            ORDER BY i.category, i.name
        """)

        items = cursor.fetchall()
        cursor.close()

        return render_template("Menu.html", 
                               session_id=session_id, 
                               table_number=table_number, 
                               items=items)