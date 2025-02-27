from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Permanent product storage (Simulating database)
products = {
    "L40": {"name": "Lace40", "price": 40},
    "L45": {"name": "Lace45", "price": 45},
    "L50": {"name": "Lace50", "price": 50},
    "L60": {"name": "Lace60", "price": 60}
}

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/search', methods=['GET'])
def search_product():
    query = request.args.get('q', '').strip().lower()
    
    matching_products = {
        code.upper(): {"name": data["name"], "price": data["price"]}
        for code, data in products.items()
        if query in data["name"].lower() or query in code.lower()
    }

    return jsonify(matching_products)

@app.route('/add_product', methods=['POST'])
def add_product():
    data = request.json
    code = data.get("code").strip().upper()
    name = data.get("name").strip()
    price = data.get("price")

    if not code or not name or not price:
        return jsonify({"status": "error", "message": "Invalid input"}), 400

    if code in products:
        return jsonify({"status": "error", "message": "Product code already exists"}), 400

    products[code] = {"name": name, "price": price}  # Save permanently
    return jsonify({"status": "success", "message": "Product added"}), 200

@app.route('/edit_product', methods=['POST'])
def edit_product():
    data = request.json
    code = data.get("code").strip().upper()
    new_name = data.get("name").strip()
    new_price = data.get("price")

    if code in products:
        products[code]["name"] = new_name
        products[code]["price"] = new_price
        return jsonify({"status": "success", "message": "Product updated successfully"}), 200

    return jsonify({"status": "error", "message": "Product not found"}), 404

@app.route('/delete_product', methods=['DELETE'])
def delete_product():
    code = request.args.get("code").strip().upper()

    if code in products:
        del products[code]
        return jsonify({"status": "success", "message": "Product deleted successfully"}), 200

    return jsonify({"status": "error", "message": "Product not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
