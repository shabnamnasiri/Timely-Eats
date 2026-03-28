from flask import render_template, redirect, session


def register_menu_routes(app, mysql):

    @app.route("/menu", methods=["GET","POST"])
    def menu():

        if "user_id" not in session:
            return redirect("/signin")


        return render_template("Menu.html")

