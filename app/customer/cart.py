from flask import render_template, redirect, session, request
import MySQLdb.cursors

def register_customer_cart_routes(app, mysql):

    # ── helpers ────────────────────────────────────────────────────────────────
    def get_open_cart_id(cursor, user_id):
        cursor.execute("""
            SELECT cart_id FROM cart
            WHERE user_id = %s AND status = 'open'
            ORDER BY cart_id DESC LIMIT 1
        """, (user_id,))
        row = cursor.fetchone()
        return row['cart_id'] if row else None

    # ── main cart view ──────────────────────────────────────────────────────────
    @app.route('/Customer/Cart')
    def customer_cart():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        user_id = session.get('user_id')
        if not user_id:
            return "User not logged in", 401

        table_number = "—"

        cart_id = get_open_cart_id(cursor, user_id)

        if not cart_id:
            return render_template('Cart.html',
                cart_items=[],
                cart_total=0,
                table_number=table_number,
                loyalty_points=0,
                loyalty_progress=0,
                points_to_next_reward=100,
                loyalty_discount='5.00',
                loyalty_discount_active=False,
                points_earned=0,
                order_placed=False,
                order_number=None,
            )

        cursor.execute("""
            SELECT ci.cart_item_id AS id, ci.quantity,
                   ci.customization_note AS note,
                   m.item_id, m.name, m.category, m.price
            FROM cart_item ci
            JOIN item m ON ci.item_id = m.item_id
            WHERE ci.cart_id = %s
        """, (cart_id,))
        raw_items = cursor.fetchall()

        cart_items = [
            {
                'id':            row['id'],
                'item_id':       row['item_id'],
                'name':          row['name'],
                'category':      row['category'],
                'price':         float(row['price']),
                'quantity':      row['quantity'],
                'note':          row['note'],
                'customisations': [],
            }
            for row in raw_items
        ]
        cart_total   = sum(i['price'] * i['quantity'] for i in cart_items)
        points_earned = int(cart_total)

        loyalty_points   = session.get('loyalty_points', 0)
        points_to_next   = max(0, 100 - (loyalty_points % 100))
        loyalty_progress = loyalty_points % 100
        loyalty_discount = '5.00'
        loyalty_discount_active = False

        # flash message passed via session
        flash_msg = session.pop('cart_flash', None)

        return render_template('Cart.html',
            cart_items=cart_items,
            cart_total=cart_total,
            table_number=table_number,
            loyalty_points=loyalty_points,
            loyalty_progress=loyalty_progress,
            points_to_next_reward=points_to_next,
            loyalty_discount=loyalty_discount,
            loyalty_discount_active=loyalty_discount_active,
            points_earned=points_earned,
            order_placed=session.pop('order_placed', False),
            order_number=session.pop('order_number', None),
            flash_msg=flash_msg,
        )

    # ── update quantity ─────────────────────────────────────────────────────────
    @app.route('/Customer/Cart/update_quantity', methods=['POST'])
    def cart_update_quantity():
        user_id = session.get('user_id')
        if not user_id:
            return "User not logged in", 401

        cart_item_id = request.form.get('cart_item_id', type=int)
        action       = request.form.get('action')   # 'increase' or 'decrease'

        if not cart_item_id or action not in ('increase', 'decrease'):
            return redirect('/Customer/Cart')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # verify the item belongs to this user's open cart
        cursor.execute("""
            SELECT ci.cart_item_id, ci.quantity
            FROM cart_item ci
            JOIN cart c ON ci.cart_id = c.cart_id
            WHERE ci.cart_item_id = %s
              AND c.user_id = %s
              AND c.status = 'open'
        """, (cart_item_id, user_id))
        row = cursor.fetchone()

        if not row:
            return redirect('/Customer/Cart')

        new_qty = row['quantity'] + (1 if action == 'increase' else -1)

        if new_qty <= 0:
            # remove the item entirely
            cursor.execute("DELETE FROM cart_item WHERE cart_item_id = %s", (cart_item_id,))
            session['cart_flash'] = ('removed', 'Item removed from your order.')
        else:
            cursor.execute(
                "UPDATE cart_item SET quantity = %s WHERE cart_item_id = %s",
                (new_qty, cart_item_id)
            )

        mysql.connection.commit()
        return redirect('/Customer/Cart')

    # ── remove item ─────────────────────────────────────────────────────────────
    @app.route('/Customer/Cart/remove_item', methods=['POST'])
    def cart_remove_item():
        user_id = session.get('user_id')
        if not user_id:
            return "User not logged in", 401

        cart_item_id = request.form.get('cart_item_id', type=int)
        if not cart_item_id:
            return redirect('/Customer/Cart')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # verify ownership before deleting
        cursor.execute("""
            SELECT ci.cart_item_id
            FROM cart_item ci
            JOIN cart c ON ci.cart_id = c.cart_id
            WHERE ci.cart_item_id = %s
              AND c.user_id = %s
              AND c.status = 'open'
        """, (cart_item_id, user_id))

        if cursor.fetchone():
            cursor.execute("DELETE FROM cart_item WHERE cart_item_id = %s", (cart_item_id,))
            mysql.connection.commit()
            session['cart_flash'] = ('removed', 'Item removed from your order.')

        return redirect('/Customer/Cart')

    # ── save special instructions ───────────────────────────────────────────────
    @app.route('/Customer/Cart/save_note', methods=['POST'])
    def cart_save_note():
        user_id = session.get('user_id')
        if not user_id:
            return "User not logged in", 401

        cart_item_id = request.form.get('cart_item_id', type=int)
        note         = request.form.get('note', '').strip()

        if not cart_item_id:
            return redirect('/Customer/Cart')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # verify ownership before updating
        cursor.execute("""
            SELECT ci.cart_item_id
            FROM cart_item ci
            JOIN cart c ON ci.cart_id = c.cart_id
            WHERE ci.cart_item_id = %s
              AND c.user_id = %s
              AND c.status = 'open'
        """, (cart_item_id, user_id))

        if cursor.fetchone():
            cursor.execute(
                "UPDATE cart_item SET customization_note = %s WHERE cart_item_id = %s",
                (note or None, cart_item_id)
            )
            mysql.connection.commit()
            session['cart_flash'] = ('saved', 'Preferences saved.')

        return redirect('/Customer/Cart')