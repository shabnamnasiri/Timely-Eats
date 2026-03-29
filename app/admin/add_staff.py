from flask import render_template, request, flash, redirect, session
from werkzeug.security import generate_password_hash
from MySQLdb import IntegrityError
import phonenumbers, re

def register_admin_add_staff_routes(app, mysql):

    @app.route("/admin/add_new_staff", methods=["GET", "POST"])
    def admin_add_staff():

        if "user_id" not in session:
            return redirect("/signin")

        if request.method == "POST":
            username = request.form.get("username")
            phone = request.form.get("phone")
            password = request.form.get("password")
            confirm_password = request.form.get("confirm_password")

            form_data = {
                "username": username,
                "phone": phone
            }

            # Password validation
            pattern = r'^(?=.*[0-9])(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$'
            if not re.match(pattern, password):
                flash("Password must be at least 8 characters long, include a number and a symbol", "error")
                return render_template("add_staff.html", form_data=form_data, staffs=[])

            if password != confirm_password:
                flash("Passwords do not match", "error")
                return render_template("add_staff.html", form_data=form_data, staffs=[])

            # Phone validation
            try:
                parsed_number = phonenumbers.parse(phone, None)
                if not phonenumbers.is_valid_number(parsed_number):
                    flash("Invalid phone number", "error")
                    return render_template("add_staff.html", form_data=form_data, staffs=[])

            except phonenumbers.NumberParseException:
                flash("Phone must start with + and country code", "error")
                return render_template("add_staff.html", form_data=form_data, staffs=[])

            cursor = mysql.connection.cursor()

            try:
                # Check duplicates (optimized)
                cursor.execute("""
                    SELECT id FROM User 
                    WHERE username=%s OR phone_number=%s
                """, (username, phone))

                if cursor.fetchone():
                    flash("Username or phone already exists", "error")
                    return render_template("add_staff.html", form_data=form_data, staffs=[])

                hashed_password = generate_password_hash(password)

                cursor.execute("""
                    INSERT INTO User (username, password, phone_number, role_id)
                    VALUES (%s,%s,%s,2)
                """, (username, hashed_password, phone))

                mysql.connection.commit()

            except IntegrityError:
                flash("Database error", "error")
                return render_template("add_staff.html", form_data=form_data, staffs=[])

            finally:
                cursor.close()

            flash("Registration successful!", "success")
            return redirect("/Admin/add_staff")

        return render_template("add_staff.html", form_data={}, staffs=[])


    @app.route("/Admin/add_staff", methods=["GET"])
    def admin_staff():

        if "user_id" not in session:
            return redirect("/login")

        cursor = mysql.connection.cursor()

        cursor.execute("""
    SELECT user_id, username, phone_number, role_id
    FROM User
    WHERE role_id = 2
""")

        staffs = cursor.fetchall()
        cursor.close()

        return render_template("add_staff.html", staffs=staffs, form_data={})