from flask import flash, redirect, session


ADMIN_ROLE_ID = 3
COMPLETED_ORDER_STATUS = "closed"


def admin_required():
    if "user_id" not in session:
        flash("Please sign in to access this page.", "warning")
        return redirect("/signin")
    if session.get("role_id") != ADMIN_ROLE_ID:
        flash("Access denied. Admins only.", "danger")
        return redirect("/signin")
    return None


def get_admin_user(mysql):
    user_id = session.get("user_id")
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT username FROM user WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    return user
