from flask import render_template, request, redirect, session


def register_add_menu_routes(app, mysql):

    @app.route("/add_menu", methods=["GET","POST"])
    def add_menu():

        if "user_id" not in session or session["role_id"] == 1 :
            return redirect("/signin")


        return render_template("Add_menu.html")
