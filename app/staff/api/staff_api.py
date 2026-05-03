from flask import jsonify, session

def register_staff_api(app, mysql):

    @app.route('/api/staff/info')
    def get_staff_info():
        if "user_id" not in session:
            return jsonify({"error": "Not logged in"}), 401

        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT user_id, username, phone_number, role_id
            FROM user
            WHERE user_id = %s
        """, (session["user_id"],))
        
        result = cursor.fetchone()
        cursor.close()

        if not result:
            return jsonify({"error": "User not found"}), 404

        return jsonify({
            "user_id": result[0],
            "username": result[1],
            "phone_number": result[2],
            "role_id": result[3]
        })