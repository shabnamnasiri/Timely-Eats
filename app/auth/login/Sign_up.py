from flask import render_template, request, flash, redirect, session, url_for
from werkzeug.security import generate_password_hash
from MySQLdb import IntegrityError
import phonenumbers, re

def register_register_routes(app, mysql):

    # ── CUSTOMER REGISTRATION ──────────────────────────────────────────
    @app.route("/signup", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username")
            phone = request.form.get("phone")
            password = request.form.get("password")
            confirm_password = request.form.get("confirm_password")

            form_data = {"username": username, "phone": phone}

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
                # Normalizing to lowercase 'user' table
                cursor.execute("SELECT username FROM user WHERE username=%s", (username,))
                if cursor.fetchone():
                    flash("Username already exists", "error")
                    return render_template("Sign_up.html", form_data=form_data)

                cursor.execute("SELECT phone_number FROM user WHERE phone_number=%s", (phone,))
                if cursor.fetchone():
                    flash("Phone already exists", "error")
                    return render_template("Sign_up.html", form_data=form_data)

                hashed_password = generate_password_hash(password)
                cursor.execute("""
                    INSERT INTO user (username, password, phone_number, role_id)
                    VALUES (%s,%s,%s,1)
                """, (username, hashed_password, phone))
                mysql.connection.commit()

                cursor.execute("SELECT user_id FROM user WHERE username=%s", (username,))
                new_user = cursor.fetchone()

            except IntegrityError:
                flash("Database error", "error")
                return render_template("Sign_up.html", form_data=form_data)
            finally:
                cursor.close()

            # Log in directly after signup
            session["user_id"] = new_user[0]
            session["role_id"] = 1
            session["username"] = username

            if session.get('table_session_id'):
                flash(f"Welcome {username}! You're all set at Table {session.get('table_number', '')}.", "success")
                return redirect("/menu")
            else:
                flash("Account created! Please scan the QR code on your table to order.", "success")
                return redirect(url_for('signin'))

        # ── GET REQUEST ──
        # Clears any background session when entering signup to give a clean slate
        session.clear()
        return render_template("Sign_up.html", form_data={})


    # ── ADMIN REGISTRATION ──────────────────────────────────────────
    # Note: Changed path from "/" to "/admin/signup" so your root path stays clear!
    @app.route("/admin/signup", methods=["GET", "POST"])
    def admin_register():
        if request.method == "POST":
            username = request.form.get("username")
            phone = request.form.get("phone")
            password = request.form.get("password")
            confirm_password = request.form.get("confirm_password")

            form_data = {"username": username, "phone": phone}

            pattern = r'^(?=.*[0-9])(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$'
            if not re.match(pattern, password):
                flash("Password must be at least 8 characters long, include a number and a symbol", "error")
                return render_template("admin_signup.html", form_data=form_data)

            if password != confirm_password:
                flash("Passwords do not match", "error")
                return render_template("admin_signup.html", form_data=form_data)

            try:
                parsed_number = phonenumbers.parse(phone)
                if not phonenumbers.is_valid_number(parsed_number):
                    flash("Invalid phone number", "error")
                    return render_template("admin_signup.html", form_data=form_data)
            except:
                flash("Phone must start with + and country code", "error")
                return render_template("admin_signup.html", form_data=form_data)

            cursor = mysql.connection.cursor()
            try:
                cursor.execute("SELECT username FROM user WHERE username=%s", (username,))
                if cursor.fetchone():
                    flash("Username already exists", "error")
                    return render_template("admin_signup.html", form_data=form_data)

                cursor.execute("SELECT phone_number FROM user WHERE phone_number=%s", (phone,))
                if cursor.fetchone():
                    flash("Phone already exists", "error")
                    return render_template("admin_signup.html", form_data=form_data)

                hashed_password = generate_password_hash(password)
                cursor.execute("""
                    INSERT INTO user (username, password, phone_number, role_id)
                    VALUES (%s,%s,%s,3)
                """, (username, hashed_password, phone))
                mysql.connection.commit()

            except IntegrityError:
                flash("Database error", "error")
                return render_template("admin_signup.html", form_data=form_data)
            finally:
                cursor.close()

            flash("Admin account created! Please sign in.", "success")
            return redirect(url_for('signin'))

        # ── GET REQUEST ──
        session.clear()
        return render_template("admin_signup.html", form_data={})