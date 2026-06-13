from flask import render_template, request, redirect, session, flash
from werkzeug.security import check_password_hash

def register_login_routes(app, mysql):
    @app.route("/signin", methods=["GET", "POST"])
    def signin():
        if "user_id" in session:
            if session.get("role_id") == 1:
                return redirect("/menu")
            elif session.get("role_id") == 2:
                return redirect("/staff/qr")
            else:
                return redirect("/admin/add_menu")

        if request.method == "POST":
            username_phone = request.form["username_phone"]
            password = request.form["password"]

            cursor = mysql.connection.cursor()
            cursor.execute(
                "SELECT user_id, password, role_id, username FROM User WHERE username=%s OR phone_number=%s",
                (username_phone, username_phone)
            )
            user = cursor.fetchone()
            cursor.close()

            if not user or not check_password_hash(user[1], password):
                flash("Invalid username or password.", "danger")
                return render_template("Sign_In.html")

            user_id  = user[0]
            role_id  = user[2]
            username = user[3]

            table_session_id = session.get("table_session_id")
            expected_user_id = session.get("expected_user_id")

            if table_session_id and expected_user_id:
                # Table is in 'ordered' state — only the owner can log in
                if user_id != expected_user_id:
                    flash(
                        "This table already has an active order in progress. "
                        "Please wait for it to be completed before placing a new one.",
                        "warning"
                    )
                    return render_template("Sign_In.html")
                # Correct user — clear the gate
                session.pop("expected_user_id", None)

            session["user_id"]  = user_id
            session["role_id"]  = role_id
            session["username"] = username

            if role_id == 1:
                return redirect("/menu")
            elif role_id == 2:
                return redirect("/staff/qr")
            else:
                return redirect("/admin/add_menu")

        return render_template("Sign_In.html")

    @app.route("/logout")
    def logout():
        username = session.get("username")
        # Preserve table session across logout so user can log back in
        table_session_id = session.get("table_session_id")
        table_number     = session.get("table_number")
        session.clear()
        if table_session_id:
            session["table_session_id"] = table_session_id
            session["table_number"]     = table_number
            session.modified = True
        response = redirect("/signin")
        response.delete_cookie('session')
        flash(f"Goodbye {username}! You have been logged out.", "success")
        return response