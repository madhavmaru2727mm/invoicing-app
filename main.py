from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Permanent product storage (Simulating database)
products = {
    "P001": {"name": "Laptop", "price": 45000},
    "P002": {"name": "Headphones", "price": 2000}
}

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/search', methods=['GET'])
def search_product():
    query = request.args.get('q', '').strip().lower()
    matching_products = {code: data for code, data in products.items() if query in data["name"].lower() or query in code.lower()}
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

