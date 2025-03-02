import mysql.connector
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure random key

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
    # Create products table with org_id column
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
    
    # Insert default products for organization 'ABC'
    org_id = "ABC"
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
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            org_id VARCHAR(10) NOT NULL,
            username VARCHAR(50) NOT NULL,
            password VARCHAR(255) NOT NULL,
            role ENUM('owner', 'employee') NOT NULL,
            PRIMARY KEY (org_id, username)
        )
    """)
    conn.commit()
    # Insert a default owner for organization 'ABC'
    default_user = ("ABC", "admin", "admin", "owner")  # username: admin, password: admin
    cursor.execute("SELECT COUNT(*) FROM users WHERE org_id = %s AND username = %s", (default_user[0], default_user[1]))
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (org_id, username, password, role) VALUES (%s, %s, %s, %s)", default_user)
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

# ----------------- Login Routes -----------------

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

# ----------------- Main Application Routes -----------------

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
    
    cursor.execute("INSERT INTO products (org_id, code, name, price) VALUES (%s, %s, %s, %s)", (org_id, code, name, price))
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
        cursor.execute("INSERT INTO products (org_id, code, name, price) VALUES (%s, %s, %s, %s)", (org_id, new_code, new_name, new_price))
        cursor.execute("DELETE FROM products WHERE org_id = %s AND code = %s", (org_id, old_code))
    else:
        cursor.execute("UPDATE products SET name = %s, price = %s WHERE org_id = %s AND code = %s", (new_name, new_price, org_id, old_code))
    
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

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
