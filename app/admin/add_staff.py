from flask import render_template, request, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash
from MySQLdb import IntegrityError
import phonenumbers, re

def register_admin_add_staff_routes(app, mysql):

    # ── helper: admin-only guard ──
    def admin_required():
        if "user_id" not in session:
            return redirect("/signin")
        if session.get("role_id") != 3:
            return redirect("/signin")
        return None

    def get_all_staff(cursor):
        cursor.execute("""
            SELECT user_id, username, phone_number, role_id
            FROM user
            WHERE role_id = 2
        """)
        return cursor.fetchall()

    @app.route("/admin/add_staff", methods=["GET"])
    def admin_staff():
        guard = admin_required()
        if guard:
            return guard

        cursor = mysql.connection.cursor()
        staffs = get_all_staff(cursor)
        cursor.close()
        return render_template("add_staff.html", staffs=staffs, form_data={})

    @app.route("/admin/add_new_staff", methods=["POST"])
    def admin_add_staff():
        guard = admin_required()
        if guard:
            return guard

        username         = request.form.get("username")
        phone            = request.form.get("phone")
        password         = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        form_data = {"username": username, "phone": phone}

        # Password validation
        pattern = r'^(?=.*[0-9])(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$'
        if not re.match(pattern, password):
            cursor = mysql.connection.cursor()
            staffs = get_all_staff(cursor)
            cursor.close()
            flash("Password must be at least 8 characters long, include a number and a symbol", "error")
            return render_template("add_staff.html", form_data=form_data, staffs=staffs)

        if password != confirm_password:
            cursor = mysql.connection.cursor()
            staffs = get_all_staff(cursor)
            cursor.close()
            flash("Passwords do not match", "error")
            return render_template("add_staff.html", form_data=form_data, staffs=staffs)

        # Phone validation
        try:
            parsed_number = phonenumbers.parse(phone, None)
            if not phonenumbers.is_valid_number(parsed_number):
                cursor = mysql.connection.cursor()
                staffs = get_all_staff(cursor)
                cursor.close()
                flash("Invalid phone number", "error")
                return render_template("add_staff.html", form_data=form_data, staffs=staffs)
        except phonenumbers.NumberParseException:
            cursor = mysql.connection.cursor()
            staffs = get_all_staff(cursor)
            cursor.close()
            flash("Phone must start with + and country code", "error")
            return render_template("add_staff.html", form_data=form_data, staffs=staffs)

        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                SELECT user_id FROM user
                WHERE username=%s OR phone_number=%s
            """, (username, phone))

            if cursor.fetchone():
                staffs = get_all_staff(cursor)
                flash("Username or phone already exists", "error")
                return render_template("add_staff.html", form_data=form_data, staffs=staffs)

            hashed_password = generate_password_hash(password)
            cursor.execute("""
                INSERT INTO user (username, password, phone_number, role_id)
                VALUES (%s, %s, %s, 2)
            """, (username, hashed_password, phone))
            mysql.connection.commit()

        except IntegrityError:
            staffs = get_all_staff(cursor)
            flash("Database error", "error")
            return render_template("add_staff.html", form_data=form_data, staffs=staffs)

        finally:
            cursor.close()

        flash("Staff member added successfully!", "success")
        return redirect(url_for('admin_staff'))

    # ── delete staff ──
    @app.route("/delete_staff/<int:user_id>", methods=["POST"])
    def delete_staff(user_id):
        guard = admin_required()
        if guard:
            return guard

        try:
            cursor = mysql.connection.cursor()
            # Only allow deleting staff (role_id=2), never admins or customers
            cursor.execute("DELETE FROM user WHERE user_id=%s AND role_id=2", (user_id,))
            mysql.connection.commit()
            cursor.close()
        except Exception as e:
            flash("Error deleting staff member", "error")

        return redirect(url_for('admin_staff'))