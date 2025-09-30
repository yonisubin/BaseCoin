from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
from secret import RESET_PASSWORD, ADMIN_USERNAME, ADMIN_PASSWORD_HASH, SQL_PASSWORD
start_balance = 200  # Default starting balance for new users
app = Flask(__name__)
app.secret_key = 'your-very-secret-key'  # Change this to a strong random value!
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql+psycopg2://neondb_owner:{SQL_PASSWORD}@ep-autumn-tree-ad4vxqzl-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
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

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)  # Store hashed passwords

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

from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    admin_username = session.get('admin_username', ADMIN_USERNAME)
    return render_template('index.html', admin_username=admin_username)

@app.route('/api/users')
@login_required
def get_users():
    users = User.query.all()
    return jsonify(
        [{'id': user.id, 'name': user.name, 'balance': user.balance, 
          'phone': user.phone, 'email': user.email, 'whatsapp': user.whatsapp, 
          "teudat_zihut" : user.teudat_zihut, "date_of_birth": user.date_of_birth} 
          for user in users])

@app.route('/api/user/<int:user_id>')
@login_required
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({'id': user.id, 'name': user.name, 'balance': user.balance})

@app.route('/user/<int:user_id>')
@login_required
def user_details(user_id):
    # This route will render the user details page based on the user ID
    user = User.query.get_or_404(user_id)
    return render_template('user_details.html', user=user)

@app.route('/api/add_user', methods=['POST'])
@login_required
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
        print("New user added:", new_user.name)
        return jsonify({"message": "User added successfully!"}, 201)
    else:
        return jsonify({"message": "User name is required!"}), 400

@app.route('/api/transfer', methods=['POST'])
@login_required
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
@login_required
def reset_balances():
    data = request.get_json()
    admin_password = data.get('password', '')

    # Check if the provided password matches the admin password
    if admin_password == RESET_PASSWORD:
        users = User.query.all()
        for user in users:
            user.balance = max(user.balance, start_balance)  # Ensure balance is not below start balance
        db.session.commit()
        return jsonify({"message": "All user balances have been reset to 200."}), 200
    else:
        return jsonify({"message": "Invalid admin password."}), 403
@app.route('/users')
@login_required
def all_users_details():
    return render_template('all_users_details.html')
@app.route('/api/spend', methods=['POST'])
@login_required
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
@login_required
def remove_user(user_id):
    user = User.query.get_or_404(user_id)

    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User removed successfully!"}), 200
    else:
        return jsonify({"message": "User not found!"}), 404
    
@app.route('/api/edit_user/<int:user_id>', methods=['POST'])
@login_required
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
@login_required
def inventory():
    items = Inventory.query.all()
    return render_template('inventory.html', items=items)

@app.route('/inventory/update/<int:item_id>', methods=['POST'])
@login_required
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
@login_required
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

from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        print(f"Attempted login with username: {username} and password: {password}")
        admin = Admin.query.filter_by(username=username).first()
        # if admin and (check_password_hash(admin.password_hash, password) or 
        #               password == ADMIN_PASSWORD_HASH or password == admin.password_hash):
        print(f"Admin from DB: {admin.username if admin else 'None'}")
        if (username==ADMIN_USERNAME and password==ADMIN_PASSWORD_HASH) or (admin and check_password_hash(admin.password_hash, password)):
            session['logged_in'] = True
            session['admin_username'] = username  # <-- Store in session
            print("Admin logged in")
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
from werkzeug.security import generate_password_hash, check_password_hash
@app.route('/add_admin', methods=['GET', 'POST'])
@login_required
def add_admin():
    # Only allow access if the logged-in user is named 'admin'
    session_admin = session.get('admin_username', '')
    if session_admin != 'admin':
        flash('Access denied: Only admin can add another admin.', 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        new_admin_username = request.form.get('username')
        new_admin_password = request.form.get('password')
        # Here you would save the new admin credentials securely (e.g., hash password and store in DB or config)
        # For demonstration, just flash a message
        flash(f'Admin {new_admin_username} added successfully!', 'success')
        # Check if username already exists
        existing_admin = Admin.query.filter_by(username=new_admin_username).first()
        if existing_admin:
            flash('Admin username already exists!', 'danger')
            return redirect(url_for('add_admin'))
        # Hash the password
        password_hash = generate_password_hash(new_admin_password)
        # Save new admin to database
        new_admin = Admin(username=new_admin_username, password_hash=password_hash)
        db.session.add(new_admin)
        db.session.commit()
        print("New admin added:", new_admin.username, new_admin_password)
        return redirect(url_for('index'))
    return render_template('add_admin.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
