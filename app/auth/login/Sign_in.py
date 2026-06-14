from flask import render_template, request, redirect, session, flash
from werkzeug.security import check_password_hash

def register_login_routes(app, mysql):
    @app.route("/signin", methods=["GET", "POST"])
    def signin():
        # If user is already logged in, redirect based on role
        if "user_id" in session:
            if session.get("role_id") == 1:
                return redirect("/menu")
            elif session.get("role_id") == 2:
                return redirect("/staff/qr")
            else:
                return redirect("/admin/add_menu")
        # Handle login form submission
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
            # Verify user exists and password is correct
            if not user or not check_password_hash(user[1], password):
                flash("Invalid username or password.", "danger")
                return render_template("Sign_In.html")
            # Set session variables
            user_id  = user[0]
            role_id  = user[2]
            username = user[3]
            # Check for active table session and enforce ownership if necessary
            table_session_id = session.get("table_session_id")
            expected_user_id = session.get("expected_user_id")
            # If there's an active table session with an expected user, only allow that user to log in
            if table_session_id and expected_user_id:
                # If the logged-in user doesn't match the expected user for the table session, block login
                if user_id != expected_user_id:
                    flash(
                        "This table already has an active order in progress. "
                        "Please wait for it to be completed before placing a new one.",
                        "warning"
                    )
                    return render_template("Sign_In.html")
                # If the logged-in user matches the expected user, allow login and clear the expected_user_id since they have now logged in
                session.pop("expected_user_id", None)
            # Set session variables for logged-in user
            session["user_id"]  = user_id
            session["role_id"]  = role_id
            session["username"] = username
            # Redirect based on role
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
        # If there was an active table session, preserve it in the new session so user can log back in and continue their order
        if table_session_id:
            session["table_session_id"] = table_session_id
            session["table_number"]     = table_number
            session.modified = True
        # Notify staff dashboard of user logout so it can update the order status if necessary
        response = redirect("/signin")
        response.delete_cookie('session')
        flash(f"Goodbye {username}! You have been logged out.", "success")
        return response