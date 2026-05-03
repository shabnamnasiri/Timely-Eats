import os
from flask import request, jsonify, render_template, Response, redirect, url_for, session
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def register_admin_add_menu_routes(app, mysql):

    # ── helper: admin-only guard ──
    def admin_required():
        if "user_id" not in session:
            return redirect("/signin")
        if session.get("role_id") != 3:
            return redirect("/signin")
        return None

    @app.route("/admin/add_menu", methods=["GET", "POST"])
    def admin_menu():
        guard = admin_required()
        if guard:
            return guard

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT item_id, name, description, preparation_time, price, category FROM item")
        items = cursor.fetchall()
        cursor.close()
        return render_template("Add_menu.html", items=items)

    @app.route("/admin/add_menu_item", methods=["POST"])
    def admin_add_menu():
        guard = admin_required()
        if guard:
            return guard

        name        = request.form.get("name")
        description = request.form.get("description")
        price       = request.form.get("price")
        prep_time   = request.form.get("prep_time")
        category    = request.form.get("category")
        photo_data      = None
        photo_mimetype  = None

        if 'photo' in request.files:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                photo_data     = file.read()
                photo_mimetype = file.mimetype

        try:
            cursor = mysql.connection.cursor()
            cursor.execute("""
                INSERT INTO item (name, description, price, preparation_time, category, photo, photo_mimetype)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (name, description, price, prep_time, category, photo_data, photo_mimetype))
            mysql.connection.commit()
            cursor.close()
        except Exception as e:
            return jsonify({'error': str(e)}), 500

        return redirect(url_for('admin_menu'))

    # ── serve photo by item_id ──
    @app.route("/item_photo/<int:item_id>")
    def item_photo(item_id):
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT photo, photo_mimetype FROM item WHERE item_id=%s", (item_id,))
            row = cursor.fetchone()
            cursor.close()
            if row and row[0]:
                return Response(row[0], mimetype=row[1])
            import base64
            blank = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")
            return Response(blank, mimetype='image/png')
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ── update item ──
    @app.route("/update_item/<int:item_id>", methods=["POST"])
    def update_item(item_id):
        guard = admin_required()
        if guard:
            return guard

        name        = request.form.get("name")
        description = request.form.get("description")
        price       = request.form.get("price")
        prep_time   = request.form.get("prep_time")
        category    = request.form.get("category")

        try:
            cursor = mysql.connection.cursor()

            if 'photo' in request.files:
                file = request.files['photo']
                if file and file.filename and allowed_file(file.filename):
                    photo_data     = file.read()
                    photo_mimetype = file.mimetype
                    cursor.execute("""
                        UPDATE item SET name=%s, description=%s, price=%s,
                        preparation_time=%s, category=%s, photo=%s, photo_mimetype=%s
                        WHERE item_id=%s
                    """, (name, description, price, prep_time, category, photo_data, photo_mimetype, item_id))
                else:
                    cursor.execute("""
                        UPDATE item SET name=%s, description=%s, price=%s,
                        preparation_time=%s, category=%s
                        WHERE item_id=%s
                    """, (name, description, price, prep_time, category, item_id))
            else:
                cursor.execute("""
                    UPDATE item SET name=%s, description=%s, price=%s,
                    preparation_time=%s, category=%s
                    WHERE item_id=%s
                """, (name, description, price, prep_time, category, item_id))

            mysql.connection.commit()
            cursor.close()
            return redirect(url_for('admin_menu'))

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ── delete item ──
    @app.route("/delete_item/<int:item_id>", methods=["POST"])
    def delete_item(item_id):
        guard = admin_required()
        if guard:
            return guard

        try:
            cursor = mysql.connection.cursor()
            cursor.execute("DELETE FROM review WHERE item_id=%s", (item_id,))
            cursor.execute("DELETE FROM cart_item WHERE item_id=%s", (item_id,))
            cursor.execute("DELETE FROM order_details WHERE item_id=%s", (item_id,))
            cursor.execute("DELETE FROM item WHERE item_id=%s", (item_id,))
            mysql.connection.commit()
            cursor.close()
            return redirect(url_for('admin_menu'))
        except Exception as e:
            return jsonify({'error': str(e)}), 500
