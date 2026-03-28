from flask import request, jsonify
import MySQLdb

def register_staff_api(app, mysql):

    # 🔹 GET ALL STAFF
    @app.route('/api/staff', methods=['GET'])
    def get_staff():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT u.user_id AS id, u.username AS name, u.phone_number,
                   r.role_name, r.role_level
            FROM User u
            JOIN Role r ON u.role_id = r.role_id
            WHERE r.role_name = 'Staff'
        """)
        staff = cursor.fetchall()
        return jsonify(staff)


    # 🔹 GET ONE STAFF
    @app.route('/api/staff/<int:id>', methods=['GET'])
    def get_one_staff(id):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT u.user_id AS id, u.username AS name, u.phone_number,
                   r.role_name
            FROM User u
            JOIN Role r ON u.role_id = r.role_id
            WHERE u.user_id=%s
        """, (id,))
        staff = cursor.fetchone()

        if not staff:
            return jsonify({"error": "Staff not found"}), 404

        return jsonify(staff)


    # 🔹 CREATE STAFF
    @app.route('/api/staff', methods=['POST'])
    def create_staff():
        data = request.get_json()

        name = data.get('name')
        password = data.get('password')
        phone = data.get('phone_number')
        role_id = 2   # Staff

        cursor = mysql.connection.cursor()

        cursor.execute("""
            INSERT INTO User (username, password, phone_number, role_id)
            VALUES (%s, %s, %s, %s)
        """, (name, password, phone, role_id))

        mysql.connection.commit()

        return jsonify({"message": "Staff created successfully"}), 201


    # 🔹 UPDATE STAFF
    @app.route('/api/staff/<int:id>', methods=['PUT'])
    def update_staff(id):
        data = request.get_json()

        name = data.get('name')
        phone = data.get('phone_number')

        cursor = mysql.connection.cursor()

        cursor.execute("""
            UPDATE User
            SET username=%s, phone_number=%s
            WHERE user_id=%s
        """, (name, phone, id))

        mysql.connection.commit()

        return jsonify({"message": "Staff updated successfully"})


    # 🔹 DELETE STAFF
    @app.route('/api/staff/<int:id>', methods=['DELETE'])
    def delete_staff(id):
        cursor = mysql.connection.cursor()

        cursor.execute("DELETE FROM User WHERE user_id=%s", (id,))
        mysql.connection.commit()

        return jsonify({"message": "Staff deleted successfully"})