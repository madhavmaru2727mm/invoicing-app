import mysql.connector, random, string, secrets, datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure random key

# In-memory store for password reset tokens (for other purposes) – unchanged
reset_tokens = {}

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="075Amm@129",
        database="invoicing_db"
    )

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Create products table (unchanged)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            org_id VARCHAR(10) NOT NULL,
            code VARCHAR(10) NOT NULL,
            name VARCHAR(255) NOT NULL,
            price DOUBLE NOT NULL,
            PRIMARY KEY (org_id, code)
        )
    """)
    conn.commit()
    # Modified users table: added email column.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            org_id VARCHAR(10) NOT NULL,
            username VARCHAR(50) NOT NULL,
            email VARCHAR(255),
            password VARCHAR(255) NOT NULL,
            role ENUM('owner', 'employee') NOT NULL,
            PRIMARY KEY (org_id, username)
        )
    """)
    conn.commit()
    
    # Insert default owner for organization 'ABC' if not exists.
    default_user = ("ABC", "admin", "admin@example.com", "admin", "owner")  # username: admin, password: admin
    cursor.execute("SELECT COUNT(*) FROM users WHERE org_id = %s AND username = %s", (default_user[0], default_user[1]))
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (org_id, username, email, password, role) VALUES (%s, %s, %s, %s, %s)", default_user)
    conn.commit()
    cursor.close()
    conn.close()

def generate_org_id(org_name):
    # Generate a simple org id using first three alphanumeric letters and a random 3-digit number.
    prefix = ''.join(filter(str.isalnum, org_name))[:3].upper()
    suffix = ''.join(random.choices(string.digits, k=3))
    return prefix + suffix

def initialize_default_products(org_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    DEFAULT_PRODUCTS = {
        "L40": {"name": "Lace40", "price": 40},
        "L45": {"name": "Lace45", "price": 45},
        "L50": {"name": "Lace50", "price": 50},
        "L60": {"name": "Lace60", "price": 60}
    }
    for code, details in DEFAULT_PRODUCTS.items():
        cursor.execute("SELECT COUNT(*) FROM products WHERE org_id = %s AND code = %s", (org_id, code))
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO products (org_id, code, name, price) VALUES (%s, %s, %s, %s)",
                           (org_id, code, details["name"], details["price"]))
    conn.commit()
    cursor.close()
    conn.close()

def get_all_products(org_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products WHERE org_id = %s", (org_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    products = {}
    for row in rows:
        products[row["code"]] = {"name": row["name"], "price": row["price"]}
    return products

# ----------------- Existing Login and Logout Routes -----------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        org_id = request.form.get('org_id').strip()
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE org_id = %s AND username = %s", (org_id, username))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and user['password'] == password:
            session['org_id'] = org_id
            session['username'] = username
            session['role'] = user['role']
            return redirect(url_for('home', org_id=org_id))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ----------------- Forgot Password (Owner Only) with OTP -----------------
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email').strip()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s AND role = 'owner'", (email,))
        owner = cursor.fetchone()
        cursor.close()
        conn.close()
        if not owner:
            return render_template('forgot_password.html', error="Email not found for any owner.")
        # Generate OTP for password reset
        otp = str(random.randint(100000, 999999))
        session['forgot_password_otp'] = otp
        session['forgot_password_email'] = email
        # For demo purposes, display OTP in the template.
        return render_template('verify_forgot_password.html', email=email, otp=otp)
    return render_template('forgot_password.html')

@app.route('/verify_forgot_password', methods=['POST'])
def verify_forgot_password():
    user_otp = request.form.get('otp').strip()
    new_password = request.form.get('new_password').strip()
    if user_otp != session.get('forgot_password_otp'):
        return render_template('verify_forgot_password.html', email=session.get('forgot_password_email'), otp=session.get('forgot_password_otp'),
                               error="Incorrect OTP. Please try again.")
    email = session.get('forgot_password_email')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password = %s WHERE email = %s AND role = 'owner'", (new_password, email))
    conn.commit()
    cursor.close()
    conn.close()
    session.pop('forgot_password_otp', None)
    session.pop('forgot_password_email', None)
    return redirect(url_for('login'))

# ----------------- New Registration with OTP Verification -----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        org_name = request.form.get('org_name').strip()
        username = request.form.get('username').strip()  # NEW field for owner's username
        email = request.form.get('email').strip()
        password = request.form.get('password').strip()
        
        if not org_name or not username or not email or not password:
            return render_template('register.html', error="All fields are required.")
        
        # Check if email already registered as an owner.
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE email = %s AND role = 'owner'", (email,))
        if cursor.fetchone()[0] > 0:
            cursor.close()
            conn.close()
            return render_template('register.html', error="This email is already registered.")
        cursor.close()
        conn.close()
        
        # Generate OTP for registration.
        otp = str(random.randint(100000, 999999))
        # Store pending registration details (including username) in session.
        session['pending_registration'] = {
            'org_name': org_name,
            'username': username,
            'email': email,
            'password': password,
            'otp': otp
        }
        # For demo purposes, the OTP is shown in the template.
        return render_template('verify_register.html', email=email, otp=otp)
    return render_template('register.html')


@app.route('/verify_otp_register', methods=['POST'])
def verify_otp_register():
    user_otp = request.form.get('otp').strip()
    pending = session.get('pending_registration')
    if not pending:
        return redirect(url_for('register'))
    if user_otp != pending['otp']:
        return render_template('verify_register.html', email=pending['email'], otp=pending['otp'],
                               error="Incorrect OTP. Please try again.")
    # OTP is verified; complete the registration.
    org_name = pending['org_name']
    username = pending['username']
    email = pending['email']
    password = pending['password']
    org_id = generate_org_id(org_name)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (org_id, username, email, password, role) VALUES (%s, %s, %s, %s, %s)",
                   (org_id, username, email, password, "owner"))
    conn.commit()
    cursor.close()
    conn.close()
    
    # Initialize default products for the new organization.
    initialize_default_products(org_id)
    session.pop('pending_registration', None)
    
    # Render a new template that shows the assigned Organization ID.
    return render_template('registration_success.html', org_id=org_id)


# ----------------- New Organization Deletion with OTP Verification -----------------
@app.route('/org/<org_id>/delete_org', methods=['GET', 'POST'])
def delete_org(org_id):
    if 'org_id' not in session or session['org_id'] != org_id or session.get('role') != 'owner':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    if request.method == 'GET':
        # Generate OTP for deletion and store in session
        otp = str(random.randint(100000, 999999))
        session['delete_org_otp'] = otp
        return render_template('verify_delete_org.html', org_id=org_id, otp=otp)
    else:
        # POST: Verify OTP and delete organization
        user_otp = request.form.get('otp').strip()
        otp_session = session.get('delete_org_otp')
        if user_otp != otp_session:
            return render_template('verify_delete_org.html', org_id=org_id, otp=otp_session,
                                   error="Incorrect OTP. Please try again.")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE org_id = %s", (org_id,))
        cursor.execute("DELETE FROM users WHERE org_id = %s", (org_id,))
        conn.commit()
        cursor.close()
        conn.close()
        session.clear()
        session.pop('delete_org_otp', None)
        return redirect(url_for('login'))
    

# ----------------- Existing Application Routes -----------------
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/org/<org_id>/')
def home(org_id):
    if 'org_id' not in session or session['org_id'] != org_id:
        return redirect(url_for('login'))
    store_name = "ABC Store"  # Could later be loaded from an organizations table.
    return render_template('home.html', org_id=org_id, store_name=store_name, user_role=session['role'])

@app.route('/org/<org_id>/search', methods=['GET'])
def search_product(org_id):
    if 'org_id' not in session or session['org_id'] != org_id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    query = request.args.get('q', '').strip().lower()
    products = get_all_products(org_id)
    if not query:
        return jsonify(products)
    matching_products = {
        code: {"name": data["name"], "price": data["price"]}
        for code, data in products.items()
        if (query in data["name"].lower() or query in code.lower())
    }
    return jsonify(matching_products)

@app.route('/org/<org_id>/add_product', methods=['POST'])
def add_product(org_id):
    if 'org_id' not in session or session['org_id'] != org_id or session.get('role') != 'owner':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    data = request.json
    code = data.get("code", "").strip().upper()
    name = data.get("name", "").strip()
    price = data.get("price")
    if not code or not name or not isinstance(price, (int, float)):
        return jsonify({"status": "error", "message": "Invalid input"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM products WHERE org_id = %s AND code = %s", (org_id, code))
    if cursor.fetchone()[0] > 0:
        cursor.close()
        conn.close()
        return jsonify({"status": "error", "message": "Product code already exists"}), 400
    cursor.execute("INSERT INTO products (org_id, code, name, price) VALUES (%s, %s, %s, %s)",
                   (org_id, code, name, price))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "message": "Product added"}), 200

@app.route('/org/<org_id>/edit_product', methods=['POST'])
def edit_product(org_id):
    if 'org_id' not in session or session['org_id'] != org_id or session.get('role') != 'owner':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    data = request.json
    old_code = data.get("code", "").strip().upper()
    new_code = data.get("new_code", "").strip().upper()
    new_name = data.get("name", "").strip()
    new_price = data.get("price")
    if not old_code or not new_code or not new_name or not isinstance(new_price, (int, float)) or new_price <= 0:
        return jsonify({"status": "error", "message": "Invalid input"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM products WHERE org_id = %s AND code = %s", (org_id, old_code))
    if cursor.fetchone()[0] == 0:
        cursor.close()
        conn.close()
        return jsonify({"status": "error", "message": "Product not found"}), 404
    if new_code != old_code:
        cursor.execute("SELECT COUNT(*) FROM products WHERE org_id = %s AND code = %s", (org_id, new_code))
        if cursor.fetchone()[0] > 0:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "New product code already exists"}), 400
        cursor.execute("INSERT INTO products (org_id, code, name, price) VALUES (%s, %s, %s, %s)",
                       (org_id, new_code, new_name, new_price))
        cursor.execute("DELETE FROM products WHERE org_id = %s AND code = %s", (org_id, old_code))
    else:
        cursor.execute("UPDATE products SET name = %s, price = %s WHERE org_id = %s AND code = %s",
                       (new_name, new_price, org_id, old_code))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "message": "Product updated successfully"}), 200

@app.route('/org/<org_id>/delete_product', methods=['DELETE'])
def delete_product(org_id):
    if 'org_id' not in session or session['org_id'] != org_id or session.get('role') != 'owner':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    code = request.args.get("code", "").strip().upper()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM products WHERE org_id = %s AND code = %s", (org_id, code))
    if cursor.fetchone()[0] > 0:
        cursor.execute("DELETE FROM products WHERE org_id = %s AND code = %s", (org_id, code))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "message": "Product deleted successfully"}), 200
    cursor.close()
    conn.close()
    return jsonify({"status": "error", "message": "Product not found"}), 404

@app.route('/org/<org_id>/add_user', methods=['GET', 'POST'])
def add_user(org_id):
    if 'org_id' not in session or session['org_id'] != org_id or session.get('role') != 'owner':
        return redirect(url_for('login'))
    error = None
    if request.method == 'POST':
        new_username = request.form.get('username').strip()
        new_password = request.form.get('password').strip()
        new_role = request.form.get('role').strip()
        if new_role not in ['owner', 'employee']:
            error = "Invalid role selected."
        elif not new_username or not new_password:
            error = "Username and password are required."
        else:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE org_id = %s AND username = %s", (org_id, new_username))
            if cursor.fetchone()['count'] > 0:
                error = "User already exists."
            else:
                cursor.execute("INSERT INTO users (org_id, username, password, role) VALUES (%s, %s, %s, %s)",
                               (org_id, new_username, new_password, new_role))
                conn.commit()
                cursor.close()
                conn.close()
                return redirect(url_for('home', org_id=org_id))
            cursor.close()
            conn.close()
    return render_template('add_user.html', org_id=org_id, error=error)

@app.route('/org/<org_id>/manage_users', methods=['GET'])
def manage_users(org_id):
    if 'org_id' not in session or session['org_id'] != org_id or session.get('role') != 'owner':
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE org_id = %s", (org_id,))
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('manage_users.html', org_id=org_id, users=users)

@app.route('/org/<org_id>/delete_user', methods=['POST'])
def delete_user(org_id):
    if 'org_id' not in session or session['org_id'] != org_id or session.get('role') != 'owner':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    username = request.form.get("username", "").strip()
    if not username:
        return jsonify({"status": "error", "message": "No username provided"}), 400
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT role FROM users WHERE org_id = %s AND username = %s", (org_id, username))
    user = cursor.fetchone()
    if not user:
        cursor.close()
        conn.close()
        return jsonify({"status": "error", "message": "User not found"}), 404
    if user['role'] == 'owner':
        cursor.execute("SELECT COUNT(*) AS count FROM users WHERE org_id = %s AND role = 'owner'", (org_id,))
        count_result = cursor.fetchone()
        if count_result['count'] <= 1:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Cannot delete the last owner. Please delete the organization instead."}), 400
    cursor.execute("DELETE FROM users WHERE org_id = %s AND username = %s", (org_id, username))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "message": "User deleted successfully"}), 200

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
