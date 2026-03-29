import os
from flask import request, jsonify, render_template, Response,redirect,url_for
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def register_admin_add_menu_routes(app, mysql):

    @app.route("/admin/add_menu_item", methods=["GET", "POST"])
    def admin_add_menu():
        if request.method == "POST":
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
                    INSERT INTO Item (name, description, price, preparation_time, category, photo, photo_mimetype)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (name, description, price, prep_time, category, photo_data, photo_mimetype))
                mysql.connection.commit()
                cursor.close()
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT item_id, name, description, preparation_time, price, category FROM Item")
        items = cursor.fetchall()
        cursor.close()
        return render_template("Add_menu.html", items=items)

    # ── serve photo by item_id ──
    @app.route("/item_photo/<int:item_id>")
    def item_photo(item_id):
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT photo, photo_mimetype FROM Item WHERE item_id=%s", (item_id,))
            row = cursor.fetchone()
            cursor.close()
            if row and row[0]:
                return Response(row[0], mimetype=row[1])
            # return a blank 1x1 transparent png if no photo
            import base64
            blank = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")
            return Response(blank, mimetype='image/png')
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ── update item ──
    @app.route("/update_item/<int:item_id>", methods=["POST"])
    def update_item(item_id):
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
                        UPDATE Item SET name=%s, description=%s, price=%s,
                        preparation_time=%s, category=%s, photo=%s, photo_mimetype=%s
                        WHERE item_id=%s
                    """, (name, description, price, prep_time, category, photo_data, photo_mimetype, item_id))
                else:
                    cursor.execute("""
                        UPDATE Item SET name=%s, description=%s, price=%s,
                        preparation_time=%s, category=%s
                        WHERE item_id=%s
                    """, (name, description, price, prep_time, category, item_id))
            else:
                cursor.execute("""
                    UPDATE Item SET name=%s, description=%s, price=%s,
                    preparation_time=%s, category=%s
                    WHERE item_id=%s
                """, (name, description, price, prep_time, category, item_id))

            mysql.connection.commit()
            cursor.close()
            return redirect(url_for('/admin/add_menu'))

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ── delete item ──
    @app.route("/delete_item/<int:item_id>", methods=["POST"])
    def delete_item(item_id):
        try:
            cursor = mysql.connection.cursor()
            # delete linked reviews first
            cursor.execute("DELETE FROM Review WHERE item_id=%s", (item_id,))
            # delete linked cart items
            cursor.execute("DELETE FROM Cart_Item WHERE item_id=%s", (item_id,))
            # delete linked order details
            cursor.execute("DELETE FROM Order_Details WHERE item_id=%s", (item_id,))
            # now safe to delete the item
            cursor.execute("DELETE FROM Item WHERE item_id=%s", (item_id,))
            mysql.connection.commit()
            cursor.close()
            return redirect(url_for('/admin/add_menu'))
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
    @app.route("/admin/add_menu", methods=["GET", "POST"])
    def admin_menu():
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT item_id, name, description, preparation_time, price, category FROM Item")
        items = cursor.fetchall()
        cursor.close()
        return render_template("Add_menu.html", items=items)