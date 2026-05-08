from flask import render_template, request, redirect, session
from werkzeug.security import generate_password_hash
import uuid
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText



def register_forgotpassword_routes(app, mysql):

    # =============================
    # 1. Отправка reset ссылки
    # =============================
    @app.route("/forgot_password", methods=["GET", "POST"])
    def forgot_password():

        if "user_id" in session:
            return redirect("/menu")

        if request.method == "POST":
            email = request.form["email"].strip().lower()

            cursor = mysql.connection.cursor()

            cursor.execute(
                "SELECT user_id FROM User WHERE email=%s",
                (email,)
            )

            user = cursor.fetchone()

            if user:
                user_id = user[0]

                # Генерация токена
                token = str(uuid.uuid4())
                expires_at = datetime.now() + timedelta(minutes=20)

                # Сохраняем токен
                cursor.execute(
                    "INSERT INTO password_resets (user_id, token, expires_at) VALUES (%s, %s, %s)",
                    (user_id, token, expires_at)
                )
                mysql.connection.commit()

                # Ссылка
                reset_link = f"http://127.0.0.1:5000/reset-password/{token}"

                # Отправка email
                send_email(email, reset_link)

            cursor.close()

        return render_template("Forgot_Password.html")

    
def send_email(to_email, reset_link):
    sender_email = "TimelyEat@gmail.com"
    sender_password = "htxb vrdr dtyb whba"
    subject = "Password Reset"
    body = f"""
Click the link to reset your password:
{reset_link}

This link is valid for 20 minutes.
"""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print("✅ Email sent successfully")

    except Exception as e:
        print("❌ Email error:", e)