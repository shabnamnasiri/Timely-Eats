from flask import render_template, request, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash
from MySQLdb import IntegrityError
import phonenumbers, re

from app.admin.helpers import admin_required, get_admin_user

def register_admin_add_staff_routes(app, mysql):

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
        user = get_admin_user(mysql)
        cursor.close()

        return render_template("add_staff.html", staffs=staffs, form_data={}, user=user)

    @app.route("/admin/add_new_staff", methods=["POST"])
    def admin_add_staff():
        guard = admin_required()
        if guard:
            return guard

        username         = request.form.get("username")
        phone            = request.form.get("phone")
        password         = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        form_data        = {"username": username, "phone": phone}

        cursor = mysql.connection.cursor()
        staffs = get_all_staff(cursor)
        user = get_admin_user(mysql)
        cursor.close()

        # ── Validation ──────────────────────────────
        pattern = r'^(?=.*[0-9])(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$'
        if not re.match(pattern, password):
            flash("Password must be at least 8 characters, include a number and a symbol.", "danger")
            return render_template("add_staff.html", form_data=form_data, staffs=staffs, user=user)  

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("add_staff.html", form_data=form_data, staffs=staffs, user=user)  

        try:
            parsed_number = phonenumbers.parse(phone, None)
            if not phonenumbers.is_valid_number(parsed_number):
                flash("Invalid phone number.", "danger")
                return render_template("add_staff.html", form_data=form_data, staffs=staffs, user=user)  
        except phonenumbers.NumberParseException:
            flash("Phone must start with + and country code.", "danger")
            return render_template("add_staff.html", form_data=form_data, staffs=staffs, user=user)  

        # ── DB Insert ────────────────────────────────
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                SELECT user_id FROM user
                WHERE username=%s OR phone_number=%s
            """, (username, phone))

            if cursor.fetchone():
                flash("Username or phone number already exists.", "warning")
                staffs = get_all_staff(cursor)
                return render_template("add_staff.html", form_data=form_data, staffs=staffs, user=user)  

            hashed_password = generate_password_hash(password)
            cursor.execute("""
                INSERT INTO user (username, password, phone_number, role_id)
                VALUES (%s, %s, %s, 2)
            """, (username, hashed_password, phone))
            mysql.connection.commit()

        except IntegrityError:
            staffs = get_all_staff(cursor)
            flash("Database error. Please try again.", "danger")
            return render_template("add_staff.html", form_data=form_data, staffs=staffs, user=user)  

        finally:
            cursor.close()

        flash(f"Staff member '{username}' added successfully!", "success")
        return redirect(url_for('admin_staff'))

    # ── EDIT STAFF ───────────────────────────────────
    @app.route("/admin/edit_staff/<int:user_id>", methods=["POST"])
    def edit_staff(user_id):
        guard = admin_required()
        if guard:
            return guard

        username         = request.form.get("username")
        phone            = request.form.get("phone")
        password         = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                SELECT user_id FROM user
                WHERE (username=%s OR phone_number=%s) AND user_id != %s
            """, (username, phone, user_id))

            if cursor.fetchone():
                flash("Username or phone number already exists.", "warning")
                return redirect(url_for('admin_staff'))

            if password:
                pattern = r'^(?=.*[0-9])(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$'
                if not re.match(pattern, password):
                    flash("Password must be at least 8 characters, include a number and symbol.", "danger")
                    return redirect(url_for('admin_staff'))

                if password != confirm_password:
                    flash("Passwords do not match.", "danger")
                    return redirect(url_for('admin_staff'))

                hashed_password = generate_password_hash(password)
                cursor.execute("""
                    UPDATE user SET username=%s, phone_number=%s, password=%s
                    WHERE user_id=%s AND role_id=2
                """, (username, phone, hashed_password, user_id))
            else:
                cursor.execute("""
                    UPDATE user SET username=%s, phone_number=%s
                    WHERE user_id=%s AND role_id=2
                """, (username, phone, user_id))

            mysql.connection.commit()
            flash(f"Staff member '{username}' updated successfully!", "success")

        except Exception:
            flash("Error updating staff member. Please try again.", "danger")
        finally:
            cursor.close()

        return redirect(url_for('admin_staff'))

    # ── DELETE STAFF ─────────────────────────────────
    @app.route("/delete_staff/<int:user_id>", methods=["POST"])
    def delete_staff(user_id):
        guard = admin_required()
        if guard:
            return guard

        cursor = mysql.connection.cursor()
        try:
            # Get username before deleting for the flash message
            cursor.execute("SELECT username FROM user WHERE user_id=%s AND role_id=2", (user_id,))
            staff = cursor.fetchone()

            if not staff:
                flash("Staff member not found.", "warning")
                return redirect(url_for('admin_staff'))

            cursor.execute("DELETE FROM user WHERE user_id=%s AND role_id=2", (user_id,))
            mysql.connection.commit()
            flash(f"Staff member '{staff[0]}' deleted successfully.", "success")

        except Exception:
            flash("Error deleting staff member. Please try again.", "danger")
        finally:
            cursor.close()

        return redirect(url_for('admin_staff'))