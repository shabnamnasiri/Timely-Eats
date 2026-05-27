from flask import request, flash, session, render_template,redirect, url_for

def register_review_routes(app, mysql):

    @app.route('/item/<int:item_id>/review-page', methods=["GET"])
    def review_page(item_id):
        
        user_id = session.get("user_id")
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT username FROM User WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()

        user_name = user[0] if user else "Guest"


        return render_template(
            "CustRating.html",
            item_id=item_id,
            user_name=user_name
        )


    @app.route('/item/<int:item_id>/review', methods=["POST"])
    def submit_review(item_id):

        user_id = session.get("user_id")

        if not user_id:
            flash("You must be logged in to submit a review", "error")
            return redirect(url_for('review_page', item_id=item_id))

        rating = request.form.get("rating")
        comment = request.form.get("comment", "").strip()
        tags = request.form.getlist("tag")

        tag_string = ",".join(tags) if tags else None


        try:
            cursor = mysql.connection.cursor()

            cursor.execute("""
                INSERT INTO Review (user_id, item_id, tag, rating, comment)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, item_id, tag_string, rating, comment))

            mysql.connection.commit()
            cursor.close()

            flash("Review submitted successfully!", "success")
            return redirect(url_for('menu', item_id=item_id))

        except Exception as e:
            flash(str(e), "error")
            return redirect(url_for('menu', item_id=item_id))
        
    @app.route('/item/<int:item_id>/reviews-display', methods=["GET"])
    def reviews_page(item_id):

        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT r.rating, r.comment, r.tag, u.username
            FROM Review r
            LEFT JOIN User u ON r.user_id = u.user_id
            WHERE r.item_id = %s
            ORDER BY r.review_id DESC
        """, (item_id,))

        reviews = cursor.fetchall()
        cursor.close()

        return render_template("reviews.html",
                            reviews=reviews,
                            item_id=item_id)