from flask import render_template, redirect, session

def register_menu_routes(app, mysql):
    @app.route("/menu", methods=["GET"])
    def menu():
        if "user_id" not in session:
            return redirect("/signin")

        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT item_id, name, description, preparation_time, price, category
            FROM Item
            ORDER BY category, name
        """)
        items = cursor.fetchall()
        cursor.close()

        return render_template("Menu.html", items=items)