from flask import render_template, request, redirect, session, flash, url_for
from werkzeug.security import check_password_hash


def register_login_routes(app, mysql):
    @app.route("/signin", methods=["GET", "POST"])
    def signin():
        if request.method == "POST":
            username_phone = request.form.get("username_phone", "").strip()
            password = request.form.get("password", "")

            if not username_phone or not password:
                flash("Please fill in all security input fields.", "danger")
                return render_template("Sign_In.html")

            cursor = mysql.connection.cursor()
            cursor.execute(
                "SELECT user_id, password, role_id, username FROM user WHERE username=%s OR phone_number=%s",
                (username_phone, username_phone)
            )
            user = cursor.fetchone()
            cursor.close()

            if user and check_password_hash(user[1], password):
                session["user_id"] = user[0]
                session["role_id"] = user[2]
                session["username"] = user[3]

                print("✅ Login success ID:", user[0], "Role:", user[2])
                flash(f"Welcome back, {user[3]}!", "success")

                if user[2] == 1:
                    return redirect("/menu")
                elif user[2] == 2:
                    return redirect("/staff/qr")
                else:
                    return redirect(url_for('admin_menu'))

            flash("Invalid username, phone number, or password.", "danger")
            return render_template("Sign_In.html")

        # ── GET REQUEST HANDLING ──
        # Wipes old active credentials when loading the login screen to prevent auto-redirect loop bugs
        session.clear()
        return render_template("Sign_In.html")

    @app.route("/logout")
    def logout():
        username = session.get("username", "User")
        session.clear()

        flash(f"Goodbye {username}! You have been logged out.", "success")
        response = redirect(url_for('signin'))
        response.delete_cookie('session')
        return response