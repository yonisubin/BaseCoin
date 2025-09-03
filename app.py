from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from secret import ADMIN_PASSWORD  
start_balance = 200  # Default starting balance for new users
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False, unique=True)  # Unique phone number
    email = db.Column(db.String(100), nullable=False)
    whatsapp = db.Column(db.String(15), nullable=True)
    teudat_zihut = db.Column(db.String(20), nullable=False) 
    date_of_birth = db.Column(db.String(10), nullable=True) 
    service_status = db.Column(db.String(50), nullable=False)
    balance = db.Column(db.Float, default=start_balance)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    teudat_zihut = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    service_status = db.Column(db.String(50), nullable=False)
    date_time = db.Column(db.DateTime, server_default=db.func.now())  # Automatically set the date and time of the transaction

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False, unique=True)
    quantity = db.Column(db.Integer, default=0)

# Flag to check if the database has been created already
db_initialized = False

@app.before_request
def create_db():
    global db_initialized
    if not db_initialized:
        try:
            db.create_all()  # Create all tables if they don't exist
            print("Database and tables created!")
            db_initialized = True  # Ensure we only create tables once
        except Exception as e:
            print(f"Error while creating tables: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/users')
def get_users():
    users = User.query.all()
    return jsonify(
        [{'id': user.id, 'name': user.name, 'balance': user.balance, 
          'phone': user.phone, 'email': user.email, 'whatsapp': user.whatsapp, 
          "teudat_zihut" : user.teudat_zihut, "date_of_birth": user.date_of_birth} 
          for user in users])

@app.route('/api/user/<int:user_id>')
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({'id': user.id, 'name': user.name, 'balance': user.balance})

@app.route('/user/<int:user_id>')
def user_details(user_id):
    # This route will render the user details page based on the user ID
    user = User.query.get_or_404(user_id)
    return render_template('user_details.html', user=user)

@app.route('/api/add_user', methods=['POST'])
def add_user():
    data = request.get_json()
    user_name = data['name']
    user_phone = data.get('phone', '')
    user_email = data.get('email', '')
    user_whatsapp = data.get('whatsapp', user_phone)
    user_tz = data.get('teudat_zihut', '')
    user_date_of_birth = data.get('date_of_birth', '')
    user_service_status = data.get('service_status', 'Other')
    # Check if the user already exists based on phone number
    existing_user = User.query.filter_by(phone=user_phone).first()
    if existing_user:
        return jsonify({"message": "User with this phone number already exists!"}), 400
    
    
    if user_name:
        new_user = User(
            name=user_name,
            balance=start_balance,
            phone=user_phone,
            email=user_email,
            whatsapp=user_whatsapp,  # <-- Fix: actually set whatsapp
            teudat_zihut=user_tz,
            date_of_birth=user_date_of_birth,
            service_status=user_service_status
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User added successfully!"}, 201)
    else:
        return jsonify({"message": "User name is required!"}), 400

@app.route('/api/transfer', methods=['POST'])
def transfer():
    data = request.get_json()
    from_user = User.query.get(data['fromUserId'])
    to_user = User.query.get(data['toUserId'])

    if from_user.balance >= float(data['amount']):
        from_user.balance -= float(data['amount'])
        to_user.balance += float(data['amount'])
        db.session.commit()
        return jsonify({"message": "Transfer successful!"}), 200
    else:
        return jsonify({"message": "Insufficient funds!"}), 400
@app.route('/api/reset_balances', methods=['POST'])
def reset_balances():
    data = request.get_json()
    admin_password = data.get('password', '')

    # Check if the provided password matches the admin password
    if admin_password == ADMIN_PASSWORD:
        users = User.query.all()
        for user in users:
            user.balance = max(user.balance, start_balance)  # Ensure balance is not below start balance
        db.session.commit()
        return jsonify({"message": "All user balances have been reset to 200."}), 200
    else:
        return jsonify({"message": "Invalid admin password."}), 403
@app.route('/users')
def all_users_details():
    return render_template('all_users_details.html')
@app.route('/api/spend', methods=['POST'])
def spend():
    data = request.get_json()
    user_id = data['userId']
    amount = float(data['amount'])
    if amount <= 0:
        return jsonify({"message": "Amount must be greater than zero!"}), 400
    user = User.query.get(user_id)
    if user and user.balance >= amount:
        user.balance -= amount
        transaction = Transaction(
            name=user.name,
            teudat_zihut=user.teudat_zihut,
            amount=amount,
            service_status=user.service_status
        )
        db.session.add(transaction)
        db.session.commit()
        return jsonify({"message": "Spend successful!"}), 200
    else:
        return jsonify({"message": "Insufficient funds or user not found!"}), 400

@app.route('/api/remove_user/<int:user_id>', methods=['POST'])
def remove_user(user_id):
    user = User.query.get_or_404(user_id)

    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User removed successfully!"}), 200
    else:
        return jsonify({"message": "User not found!"}), 404
    
@app.route('/api/edit_user/<int:user_id>', methods=['POST'])
def edit_user(user_id):
    data = request.get_json()
    user = User.query.get_or_404(user_id)

    user.name = data.get('name', user.name)
    user.phone = data.get('phone', user.phone)
    user.email = data.get('email', user.email)
    user.whatsapp = data.get('whatsapp', user.whatsapp)
    user.teudat_zihut = data.get('teudat_zihut', user.teudat_zihut)
    user.date_of_birth = data.get('date_of_birth', user.date_of_birth)
    user.service_status = data.get('service_status', user.service_status)

    db.session.commit()
    return jsonify({"message": "User updated successfully!"}), 200

@app.route('/inventory')
def inventory():
    items = Inventory.query.all()
    return render_template('inventory.html', items=items)

@app.route('/inventory/update/<int:item_id>', methods=['POST'])
def update_inventory(item_id):
    item = Inventory.query.get_or_404(item_id)
    action = request.form.get('action')
    if action == 'increment':
        item.quantity += 1
    elif action == 'decrement' and item.quantity > 0:
        item.quantity -= 1
    if item.quantity == 0:
        db.session.delete(item)
    db.session.commit()
    return redirect(url_for('inventory'))

@app.route('/inventory/add', methods=['POST'])
def add_inventory():
    item_name = request.form.get('item_name')
    quantity = int(request.form.get('quantity', 0))
    if item_name:
        existing = Inventory.query.filter_by(item_name=item_name).first()
        if not existing:
            new_item = Inventory(item_name=item_name, quantity=quantity)
            db.session.add(new_item)
            db.session.commit()
    return redirect(url_for('inventory'))

if __name__ == '__main__':
    app.run(debug=True, host="192.168.1.34", port=5000)
    # app.run()
