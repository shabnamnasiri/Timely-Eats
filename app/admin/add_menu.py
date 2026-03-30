from flask import request, jsonify, render_template, Response,redirect,url_for,session

#allowed pic extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def register_admin_add_menu_routes(app, mysql):
    #adding each item to menu
    @app.route("/admin/add_menu_item", methods=["GET", "POST"])
    def admin_add_menu():
        if request.method == "POST":
            #getting input
            name        = request.form.get("name")
            description = request.form.get("description")
            price       = request.form.get("price")
            prep_time   = request.form.get("prep_time")
            category    = request.form.get("category")
            photo_data      = None
            photo_mimetype  = None
            #checking photo if it pass conditions and saving 
            if 'photo' in request.files:
                file = request.files['photo']
                if file and allowed_file(file.filename):
                    photo_data     = file.read()
                    photo_mimetype = file.mimetype
            #add to db
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
        #listing all from db
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT item_id, name, description, preparation_time, price, category FROM Item")
        items = cursor.fetchall()
        cursor.close()
        #passing the items to main admin page
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
        
    #displaying admin main page items
    @app.route("/admin/add_menu", methods=["GET", "POST"])
    def admin_menu():
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT item_id, name, description, preparation_time, price, category FROM Item")
        items = cursor.fetchall()
        cursor.close()
        return render_template("Add_menu.html", items=items,
                               username=session.get("username", "Admin"))
    