from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Permanent product storage (Simulating database)
products = {
    "Laptop": 45000,
    "Headphones": 2000
}

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/search', methods=['GET'])
def search_product():
    query = request.args.get('q', '').strip().lower()
    matching_products = {name: price for name, price in products.items() if query in name.lower()}
    return jsonify(matching_products)

@app.route('/add_product', methods=['POST'])
def add_product():
    data = request.json
    name = data.get("name").strip()
    price = data.get("price")

    if not name or not price:
        return jsonify({"status": "error", "message": "Invalid input"}), 400
    
    products[name] = price  # Save permanently
    return jsonify({"status": "success", "message": "Product added"}), 200

if __name__ == '__main__':
    app.run(debug=True)
