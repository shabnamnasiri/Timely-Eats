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

