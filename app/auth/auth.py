from flask import session, redirect
from functools import wraps


def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            return redirect("/signin")

        return f(*args, **kwargs)

    return decorated_function


def role_required(role_id):

    def decorator(f):

        @wraps(f)
        def decorated_function(*args, **kwargs):

            if "user_id" not in session:
                return redirect("/signin")

            if session["role_id"] != role_id:
                return "Access denied"

            return f(*args, **kwargs)

        return decorated_function

    return decorator