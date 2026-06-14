from flask import render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash
from MySQLdb import IntegrityError
import re

from app.admin.helpers import admin_required, get_admin_user


def register_admin_customer_routes(app, mysql):

    def get_all_customers(cursor):
        cursor.execute("""
            SELECT user_id, username, email, phone_number, loyalty_point
            FROM user
            WHERE role_id = 1
            ORDER BY username ASC
        """)
        return cursor.fetchall()

    # ── LIST CUSTOMERS ───────────────────────────────
    @app.route("/admin/customers", methods=["GET"])
    def admin_customers():
        guard = admin_required()
        if guard:
            return guard

        cursor = mysql.connection.cursor()
        customers = get_all_customers(cursor)
        user = get_admin_user(mysql)
        cursor.close()

        return render_template("Admin_customer.html", customers=customers, user=user)

    # ── ADD CUSTOMER ─────────────────────────────────
    @app.route("/admin/add_customer", methods=["POST"])
    def admin_add_customer():
        guard = admin_required()
        if guard:
            return guard

        first_name = request.form.get("first_name", "").strip()
        last_name  = request.form.get("last_name", "").strip()
        email      = request.form.get("email", "").strip()
        phone      = request.form.get("phone", "").strip()
        password   = request.form.get("password", "")
        status     = request.form.get("status", "New")   # "New" or "VIP" — stored in loyalty_point

        username = f"{first_name} {last_name}".strip()

        if not username or not email or not password:
            flash("First name, email and password are required.", "danger")
            return redirect(url_for("admin_customers"))

        pattern = r'^(?=.*[0-9])(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$'
        if not re.match(pattern, password):
            flash("Password must be at least 8 characters, include a number and a symbol.", "danger")
            return redirect(url_for("admin_customers"))

        # Map status to an initial loyalty_point value (business rule: VIP starts at 100)
        initial_loyalty = 100 if status == "VIP" else 0

        cursor = mysql.connection.cursor()
        try:
            cursor.execute(
                "SELECT user_id FROM user WHERE email = %s OR username = %s",
                (email, username),
            )
            if cursor.fetchone():
                flash("A customer with that email or name already exists.", "warning")
                return redirect(url_for("admin_customers"))

            hashed = generate_password_hash(password)
            cursor.execute(
                """
                INSERT INTO user (username, password, phone_number, role_id, email, loyalty_point)
                VALUES (%s, %s, %s, 1, %s, %s)
                """,
                (username, hashed, phone or None, email, initial_loyalty),
            )
            mysql.connection.commit()
            flash(f"Customer '{username}' created successfully!", "success")

        except IntegrityError:
            flash("Database error — username or email already exists.", "danger")
        finally:
            cursor.close()

        return redirect(url_for("admin_customers"))

    # ── EDIT CUSTOMER ────────────────────────────────
    @app.route("/admin/edit_customer/<int:user_id>", methods=["POST"])
    def edit_customer(user_id):
        guard = admin_required()
        if guard:
            return guard

        username = request.form.get("username", "").strip()
        email    = request.form.get("email", "").strip()
        phone    = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")

        if not username or not email:
            flash("Name and email are required.", "danger")
            return redirect(url_for("admin_customers"))

        cursor = mysql.connection.cursor()
        try:
            # Conflict check: same username/email on a *different* user
            cursor.execute(
                """
                SELECT user_id FROM user
                WHERE (username = %s OR email = %s) AND user_id != %s
                """,
                (username, email, user_id),
            )
            if cursor.fetchone():
                flash("Another customer already uses that name or email.", "warning")
                return redirect(url_for("admin_customers"))

            if password:
                pattern = r'^(?=.*[0-9])(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$'
                if not re.match(pattern, password):
                    flash("Password must be at least 8 characters, include a number and a symbol.", "danger")
                    return redirect(url_for("admin_customers"))
                if password != confirm:
                    flash("Passwords do not match.", "danger")
                    return redirect(url_for("admin_customers"))

                hashed = generate_password_hash(password)
                cursor.execute(
                    """
                    UPDATE user
                    SET username = %s, email = %s, phone_number = %s, password = %s
                    WHERE user_id = %s AND role_id = 1
                    """,
                    (username, email, phone or None, hashed, user_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE user
                    SET username = %s, email = %s, phone_number = %s
                    WHERE user_id = %s AND role_id = 1
                    """,
                    (username, email, phone or None, user_id),
                )

            mysql.connection.commit()
            flash(f"Customer '{username}' updated successfully!", "success")

        except Exception as e:
            flash(f"Error updating customer: {str(e)}", "danger")
        finally:
            cursor.close()

        return redirect(url_for("admin_customers"))

    # ── DELETE CUSTOMER ──────────────────────────────
    @app.route("/admin/delete_customer/<int:user_id>", methods=["POST"])
    def delete_customer(user_id):
        guard = admin_required()
        if guard:
            return guard

        cursor = mysql.connection.cursor()
        try:
            cursor.execute(
                "SELECT username FROM user WHERE user_id = %s AND role_id = 1",
                (user_id,),
            )
            customer = cursor.fetchone()
            if not customer:
                flash("Customer not found.", "warning")
                return redirect(url_for("admin_customers"))

            # Clean up dependent rows before deleting the user
            cursor.execute(
                "DELETE ci FROM cart_item ci JOIN cart c ON c.cart_id = ci.cart_id WHERE c.user_id = %s",
                (user_id,),
            )
            cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM review WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM user WHERE user_id = %s AND role_id = 1", (user_id,))
            mysql.connection.commit()
            flash(f"Customer '{customer[0]}' deleted successfully.", "success")

        except Exception as e:
            flash(f"Error deleting customer: {str(e)}", "danger")
        finally:
            cursor.close()

        return redirect(url_for("admin_customers"))