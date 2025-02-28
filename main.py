# Main.py - No changes needed in the backend
import json
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

PRODUCTS_FILE = "products.json"

# Default product list
DEFAULT_PRODUCTS = {
    "L40": {"name": "Lace40", "price": 40},
    "L45": {"name": "Lace45", "price": 45},
    "L50": {"name": "Lace50", "price": 50},
    "L60": {"name": "Lace60", "price": 60}
}

# Load products from file or initialize with defaults
def load_products():
    try:
        with open(PRODUCTS_FILE, "r") as file:
            products = json.load(file)
            if not isinstance(products, dict):
                products = {}

            # Merge default products if they are missing
            for code, details in DEFAULT_PRODUCTS.items():
                if code not in products:
                    products[code] = details
            
            return products
    except (FileNotFoundError, json.JSONDecodeError):
        return DEFAULT_PRODUCTS

# Save products to file
def save_products(products):
    with open(PRODUCTS_FILE, "w") as file:
        json.dump(products, file, indent=4)

# Load products at startup
products = load_products()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/search', methods=['GET'])
def search_product():
    query = request.args.get('q', '').strip().lower()

    # If no query, return all products (Fix for dropdown issue)
    if not query:
        return jsonify(products)

    matching_products = {
        code: {"name": data["name"], "price": data["price"]}
        for code, data in products.items()
        if isinstance(data, dict) and (query in data["name"].lower() or query in code.lower())
    }

    return jsonify(matching_products)

@app.route('/add_product', methods=['POST'])
def add_product():
    global products
    data = request.json
    code = data.get("code", "").strip().upper()
    name = data.get("name", "").strip()
    price = data.get("price")

    if not code or not name or not isinstance(price, (int, float)):
        return jsonify({"status": "error", "message": "Invalid input"}), 400

    if code in products:
        return jsonify({"status": "error", "message": "Product code already exists"}), 400

    products[code] = {"name": name, "price": price}
    save_products(products)

    return jsonify({"status": "success", "message": "Product added"}), 200

@app.route('/edit_product', methods=['POST'])
def edit_product():
    global products
    data = request.json
    code = data.get("code", "").strip().upper()
    new_name = data.get("name", "").strip()
    new_price = data.get("price")

    if code in products:
        products[code]["name"] = new_name
        products[code]["price"] = new_price
        save_products(products)

        return jsonify({"status": "success", "message": "Product updated successfully"}), 200

    return jsonify({"status": "error", "message": "Product not found"}), 404

@app.route('/delete_product', methods=['DELETE'])
def delete_product():
    global products
    code = request.args.get("code", "").strip().upper()

    if code in products:
        del products[code]
        save_products(products)
        return jsonify({"status": "success", "message": "Product deleted successfully"}), 200

    return jsonify({"status": "error", "message": "Product not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)