from flask import render_template, redirect, session, flash, request
import MySQLdb.cursors

def register_customer_place_order_routes(app, mysql):
    @app.route('/Customer/PlaceOrder')
    def place_order():
        payment_method = request.form.get('payment_method')
        
        if payment_method == 'cash':
            # insert order, set status = 'pending cash'
            # notify staff
            return redirect('/order/success')
        
        elif payment_method == 'card':
            # insert order, set status = 'pending payment'
            # call payment gateway
            return redirect('/order/success')

