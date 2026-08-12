from flask import flash, redirect, session


ADMIN_ROLE_ID = 3
# Orders with this status are treated as "done" for reporting purposes
# (revenue, customer spend, table stats, etc.).
COMPLETED_ORDER_STATUS = "ready"


def admin_required():
    # Must be logged in...
    if "user_id" not in session:
        flash("Please sign in to access this page.", "warning")
        return redirect("/signin")
    # ...and must be an admin (role_id == 3).
    if session.get("role_id") != ADMIN_ROLE_ID:
        flash("Access denied. Admins only.", "danger")
        return redirect("/signin")
    return None


def get_admin_user(mysql):
    # Look up the currently logged-in admin's username (for display in templates).
    user_id = session.get("user_id")
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT username FROM user WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    return user