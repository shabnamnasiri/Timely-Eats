from flask import request, session, redirect, render_template, flash
import werkzeug.security as security


def register_profile_routes(app, mysql):
    @app.route("/customer/profile", methods=["GET"])
    def view_profile():
        user_id = session.get("user_id")
        if not user_id:
            flash("Please log in to access your profile.", "error")
            return redirect("/signin")

        session_id = session.get('table_session_id')

        cur = mysql.connection.cursor()
        cur.execute("SELECT username, email, phone_number, loyalty_point FROM user WHERE user_id = %s", (user_id,))
        user_row = cur.fetchone()
        cur.close()

        if not user_row:
            flash("User record not found.", "error")
            return redirect("/signin")

        user_data = {
            "username": user_row[0],
            "email": user_row[1],
            "phone_number": user_row[2],
            "loyalty_point": user_row[3]
        }

        return render_template('profile.html', user=user_data, session_id=session_id)

    @app.route("/customer/profile/update-info", methods=["POST"])
    def update_info():
        """Handles updating both the account username and phone number details."""
        user_id = session.get("user_id")
        if not user_id:
            return redirect("/signin")

        new_username = request.form.get('username', '').strip()
        new_phone = request.form.get('phone_number', '').strip()

        if not new_username:
            flash("Username cannot be empty.", "error")
            return redirect("/customer/profile")

        cur = mysql.connection.cursor()

        # Check if username is already taken by another user
        cur.execute("SELECT user_id FROM user WHERE username = %s AND user_id != %s", (new_username, user_id))
        if cur.fetchone():
            cur.close()
            flash("That username is already taken.", "error")
            return redirect("/customer/profile")

        # Update username and phone number elements in the DB
        cur.execute(
            "UPDATE user SET username = %s, phone_number = %s WHERE user_id = %s",
            (new_username, new_phone if new_phone else None, user_id)
        )
        mysql.connection.commit()
        cur.close()

        # Update session username context to maintain state consistency across pages
        session["username"] = new_username

        flash("Profile info updated successfully!", "success")
        return redirect("/customer/profile")

    @app.route("/customer/profile/update-password", methods=["POST"])
    def update_password():
        user_id = session.get("user_id")
        if not user_id:
            return redirect("/signin")

        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash("New passwords do not match.", "error")
            return redirect("/customer/profile")

        cur = mysql.connection.cursor()
        cur.execute("SELECT password FROM user WHERE user_id = %s", (user_id,))
        user_record = cur.fetchone()

        if not user_record or not security.check_password_hash(user_record[0], current_password):
            cur.close()
            flash("Incorrect current password.", "error")
            return redirect("/customer/profile")

        hashed_password = security.generate_password_hash(new_password)
        cur.execute("UPDATE user SET password = %s WHERE user_id = %s", (hashed_password, user_id))
        mysql.connection.commit()
        cur.close()

        flash("Password updated successfully!", "success")
        return redirect("/customer/profile")