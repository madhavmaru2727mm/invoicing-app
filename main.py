import mysql.connector
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Database connection details
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="075Amm@129",
        database="invoicing_db"
    )

DEFAULT_PRODUCTS = {
    "L40": {"name": "Lace40", "price": 40},
    "L45": {"name": "Lace45", "price": 45},
    "L50": {"name": "Lace50", "price": 50},
    "L60": {"name": "Lace60", "price": 60}
}

# Initialize the database: create table if not exists and merge in default products if missing
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            code VARCHAR(10) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            price DOUBLE NOT NULL
        )
    """)
    conn.commit()
    
    # Merge default products if they are missing
    for code, details in DEFAULT_PRODUCTS.items():
        cursor.execute("SELECT COUNT(*) FROM products WHERE code = %s", (code,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO products (code, name, price) VALUES (%s, %s, %s)", 
                           (code, details["name"], details["price"]))
    conn.commit()
    cursor.close()
    conn.close()

# Helper function to retrieve all products from the database
def get_all_products():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    products = {}
    for row in rows:
        products[row["code"]] = {"name": row["name"], "price": row["price"]}
    return products

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/search', methods=['GET'])
def search_product():
    query = request.args.get('q', '').strip().lower()
    products = get_all_products()
    
    # If no query, return all products
    if not query:
        return jsonify(products)
    
    matching_products = {
        code: {"name": data["name"], "price": data["price"]}
        for code, data in products.items()
        if (query in data["name"].lower() or query in code.lower())
    }
    
    return jsonify(matching_products)

@app.route('/add_product', methods=['POST'])
def add_product():
    data = request.json
    code = data.get("code", "").strip().upper()
    name = data.get("name", "").strip()
    price = data.get("price")
    
    if not code or not name or not isinstance(price, (int, float)):
        return jsonify({"status": "error", "message": "Invalid input"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM products WHERE code = %s", (code,))
    if cursor.fetchone()[0] > 0:
        cursor.close()
        conn.close()
        return jsonify({"status": "error", "message": "Product code already exists"}), 400
    
    cursor.execute("INSERT INTO products (code, name, price) VALUES (%s, %s, %s)", (code, name, price))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"status": "success", "message": "Product added"}), 200

@app.route('/edit_product', methods=['POST'])
def edit_product():
    data = request.json
    old_code = data.get("code", "").strip().upper()
    new_code = data.get("new_code", "").strip().upper()
    new_name = data.get("name", "").strip()
    new_price = data.get("price")
    
    if not old_code or not new_code or not new_name or not isinstance(new_price, (int, float)) or new_price <= 0:
        return jsonify({"status": "error", "message": "Invalid input"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM products WHERE code = %s", (old_code,))
    if cursor.fetchone()[0] == 0:
        cursor.close()
        conn.close()
        return jsonify({"status": "error", "message": "Product not found"}), 404
    
    if new_code != old_code:
        cursor.execute("SELECT COUNT(*) FROM products WHERE code = %s", (new_code,))
        if cursor.fetchone()[0] > 0:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "New product code already exists"}), 400
        # Create new entry and delete old
        cursor.execute("INSERT INTO products (code, name, price) VALUES (%s, %s, %s)", (new_code, new_name, new_price))
        cursor.execute("DELETE FROM products WHERE code = %s", (old_code,))
    else:
        cursor.execute("UPDATE products SET name = %s, price = %s WHERE code = %s", (new_name, new_price, old_code))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"status": "success", "message": "Product updated successfully"}), 200

@app.route('/delete_product', methods=['DELETE'])
def delete_product():
    code = request.args.get("code", "").strip().upper()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM products WHERE code = %s", (code,))
    if cursor.fetchone()[0] > 0:
        cursor.execute("DELETE FROM products WHERE code = %s", (code,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "message": "Product deleted successfully"}), 200
    
    cursor.close()
    conn.close()
    return jsonify({"status": "error", "message": "Product not found"}), 404

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
