import re

from MySQLdb import IntegrityError
from flask import jsonify, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash

from app.admin.helpers import admin_required, get_admin_user




def register_admin_list_customer_routes(app, mysql):
    def get_all_customers(cursor):
        cursor.execute(
            """
            SELECT user_id, username, email, phone_number, loyalty_point
            FROM user
            WHERE role_id = 1
            ORDER BY username ASC
            """
        )
        return cursor.fetchall()

    @app.route("/admin/list_customer", methods=["GET"])
    def admin_customers():
        guard = admin_required()
        if guard:
            return guard

        cursor = mysql.connection.cursor()
        customers = get_all_customers(cursor)
        user = get_admin_user(mysql)
        cursor.close()

        return render_template("Admin_customer.html", customers=customers, user=user)

    @app.route("/admin/customers", methods=["GET"])
    def admin_customers_redirect():
        guard = admin_required()
        if guard:
            return guard
        return redirect(url_for("admin_customers"))

    @app.route("/admin/list_customer/<int:user_id>", methods=["GET"])
    def admin_customer_read(user_id):
        guard = admin_required()
        if guard:
            return guard

        cursor = mysql.connection.cursor()
        cursor.execute(
            """
            SELECT user_id, username, email, phone_number, loyalty_point
            FROM user
            WHERE role_id = 1 AND user_id = %s
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        cursor.close()

        if not row:
            return jsonify({"error": "Customer not found"}), 404

        return jsonify(
            {
                "user_id": row[0],
                "username": row[1],
                "email": row[2],
                "phone_number": row[3],
                "loyalty_point": row[4],
            }
        )

