from flask import render_template, request, redirect, session
from werkzeug.security import check_password_hash


def register_login_routes(app, mysql):

    @app.route("/signin", methods=["GET","POST"])
    def signin():
        #checking if user is already logged in
        if "user_id" in session:
            
            if session.get("role_id") == 1:
                    return redirect("/menu")
                
            elif session.get("role_id") == 2:
                    return redirect("/staff")
                
            else:
                    return redirect("/admin/add_menu")

        #sign in button actions
        if request.method == "POST":

            username_phone = request.form["username_phone"]
            password = request.form["password"]

            cursor = mysql.connection.cursor()

            cursor.execute(
                "SELECT user_id, password, role_id FROM User WHERE username=%s OR phone_number=%s",
                (username_phone, username_phone)
            )

            user = cursor.fetchone()

            cursor.close()

            #checking passsword
            if user and check_password_hash(user[1], password):
                session["user_id"] = user[0]
                session["role_id"] = user[2]
                if user[2]==1:
                    return redirect("/menu")
                elif user[2]==2:
                    return redirect("/staff")
                else: 
                    return redirect("/admin/add_menu")

            return "Invalid username or password"

        return render_template("Sign_In.html")
