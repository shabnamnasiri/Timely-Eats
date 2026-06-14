from flask import request, jsonify, render_template, Response, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from app.admin.helpers import admin_required, get_admin_user

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def register_admin_add_menu_routes(app, mysql):

    @app.route("/admin/add_menu", methods=["GET", "POST"])
    def admin_menu():
        guard = admin_required()
        if guard:
            return guard

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT item_id, name, description, preparation_time, price, category FROM item")
        items = cursor.fetchall()
        user = get_admin_user(mysql)
        cursor.close()

        return render_template("Add_menu.html", items=items, user=user)

    @app.route("/admin/add_menu_item", methods=["POST"])
    def admin_add_menu():
        guard = admin_required()
        if guard:
            return guard
        # Extract form data
        name        = request.form.get("name")
        description = request.form.get("description")
        price       = request.form.get("price")
        prep_time   = request.form.get("prep_time")
        category    = request.form.get("category")
        photo_data      = None
        photo_mimetype  = None
        # Basic validation
        if not name or not price or not category:
            flash("Name, price and category are required.", "danger")
            return redirect(url_for('admin_menu'))
        # Handle photo upload if provided
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename:
                if allowed_file(file.filename):
                    photo_data     = file.read()
                    photo_mimetype = file.mimetype
                else:
                    flash("Invalid file type. Allowed: png, jpg, jpeg, webp.", "danger")
                    return redirect(url_for('admin_menu'))
        # Insert new item into database
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("""
                INSERT INTO item (name, description, price, preparation_time, category, photo, photo_mimetype)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (name, description, price, prep_time, category, photo_data, photo_mimetype))
            mysql.connection.commit()
            cursor.close()
            flash(f"'{name}' added to menu successfully!", "success")
        # Handle database errors gracefully
        except Exception as e:
            flash(f"Database error: {str(e)}", "danger")
        # Redirect back to the admin menu page after processing
        return redirect(url_for('admin_menu'))

    #serve photo by item_id
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

    #update item 
    @app.route("/update_item/<int:item_id>", methods=["POST"])
    def update_item(item_id):
        guard = admin_required()
        if guard:
            return guard
        # Extract form data
        name        = request.form.get("name")
        description = request.form.get("description")
        price       = request.form.get("price")
        prep_time   = request.form.get("prep_time")
        category    = request.form.get("category")
        # Basic validation
        try:
            cursor = mysql.connection.cursor()

            if 'photo' in request.files:
                file = request.files['photo']
                if file and file.filename:
                    if not allowed_file(file.filename):
                        flash("Invalid file type. Allowed: png, jpg, jpeg, webp.", "danger")
                        return redirect(url_for('admin_menu'))
                    # If a new photo is uploaded, we read it and update the photo data and mimetype in the database. If no new photo is uploaded, we leave the existing photo unchanged.
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
            flash(f"'{name}' updated successfully!", "success")

        except Exception as e:
            flash(f"Error updating item: {str(e)}", "danger")

        return redirect(url_for('admin_menu'))

    # delete item
    @app.route("/delete_item/<int:item_id>", methods=["POST"])
    def delete_item(item_id):
        guard = admin_required()
        if guard:
            return guard

        try:
            cursor = mysql.connection.cursor()
            # Get name before deleting for flash message
            cursor.execute("SELECT name FROM item WHERE item_id=%s", (item_id,))
            item = cursor.fetchone()

            if not item:
                flash("Item not found.", "warning")
                return redirect(url_for('admin_menu'))

            cursor.execute("DELETE FROM review WHERE item_id=%s", (item_id,))
            cursor.execute("DELETE FROM cart_item WHERE item_id=%s", (item_id,))
            cursor.execute("DELETE FROM order_details WHERE item_id=%s", (item_id,))
            cursor.execute("DELETE FROM item WHERE item_id=%s", (item_id,))
            mysql.connection.commit()
            cursor.close()
            flash(f"'{item[0]}' deleted from menu successfully.", "success")

        except Exception as e:
            flash(f"Error deleting item: {str(e)}", "danger")

        return redirect(url_for('admin_menu'))
