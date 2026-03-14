from flask import render_template, request, flash, redirect, session
from werkzeug.security import generate_password_hash
from MySQLdb import IntegrityError
import phonenumbers, re


def register_register_routes(app, mysql):

    @app.route("/signup", methods=["GET", "POST"])
    def register():

        if "user_id" in session:
            return redirect("/menu")

        if request.method == "POST":
            username = request.form.get("username")
            phone = request.form.get("phone")
            password = request.form.get("password")
            confirm_password = request.form.get("confirm_password")

            form_data = {
             "username": username,
            "phone": phone}

            pattern = r'^(?=.*[0-9])(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$'
            if not re.match(pattern, password):
                flash("Password must be at least 8 characters long, include a number and a symbol", "error")
                return render_template("Sign_up.html", form_data=form_data)
            if password != confirm_password:
                flash("Passwords do not match", "error")
                return render_template("Sign_up.html", form_data=form_data)

            try:
                parsed_number = phonenumbers.parse(phone)

                if not phonenumbers.is_valid_number(parsed_number):
                    flash("Invalid phone number", "error")
                    return render_template("Sign_up.html", form_data=form_data)

            except:
                flash("Phone must start with + and country code", "error")
                return render_template("Sign_up.html", form_data=form_data)

            cursor = mysql.connection.cursor()

            try:

                cursor.execute(
                    "SELECT username FROM User WHERE username=%s",
                    (username,)
                )

                if cursor.fetchone():
                    flash("Username already exists", "error")
                    return render_template("Sign_up.html", form_data=form_data)

                cursor.execute(
                    "SELECT phone_number FROM User WHERE phone_number=%s",
                    (phone,)
                )

                if cursor.fetchone():
                    flash("Phone already exists", "error")
                    return render_template("Sign_up.html", form_data=form_data)

                hashed_password = generate_password_hash(password)

                cursor.execute("""
                    INSERT INTO User (username, password, phone_number, role_id)
                    VALUES (%s,%s,%s,1)
                """, (username, hashed_password, phone))

                mysql.connection.commit()

            except IntegrityError:
                flash("Database error", "error")
                return render_template("Sign_up.html", form_data=form_data)

            finally:
                cursor.close()

            flash("Registration successful!", "success")
            return redirect("/signin")

        return render_template("Sign_up.html", form_data={})