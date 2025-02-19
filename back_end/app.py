from flask import Flask, render_template, request, jsonify, send_from_directory
from collections import defaultdict
from flask_cors import CORS  # Added for CORS support
import json
import os
from datetime import datetime

app = Flask(__name__, template_folder="../front_end/templates", static_folder="../front_end/static")
CORS(app)  # Allow frontend from different origins to call the API

# Route to serve JSON files from the data directory
@app.route('/data/<filename>')
def get_json_data(filename):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, '../data')

    if os.path.exists(os.path.join(file_path, filename)):
        return send_from_directory(file_path, filename)
    else:
        return jsonify({"error": "File not found"}), 404

# Helper function to load JSON data
def load_json(file_name):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, f'../data/{file_name}')
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/backend')
def backend():
    return render_template('backend.html')

@app.route('/lookup', methods=['POST'])
def lookup_customer():
    query = request.form.get('name', '').strip().lower()
    if not query:
        return jsonify(result=[])

    customers = load_json('tory_burch_customers.json')
    purchase_history = load_json('tory_burch_purchase_history.json')
    products = load_json('tory_burch_products.json')

    result = []
    for customer in customers:
        full_name = f"{customer['first_name']} {customer['last_name']}".lower()
        if query == customer['customer_id'] or query in full_name:
            customer_purchases = []
            grouped_purchases = defaultdict(list)

            for h in purchase_history:
                if h['customer_id'] == customer['customer_id']:
                    style_number = h['product_id'].split('-')[0]  # Extract style number (ignores color)

                    # ✅ Format dates correctly
                    try:
                        raw_date = h.get("date", "Unknown Date").strip()
                        if "/" in raw_date:
                            formatted_date = datetime.strptime(raw_date, "%m/%d/%Y").strftime("%Y-%m-%d")
                        else:
                            formatted_date = datetime.strptime(raw_date, "%Y-%m-%d").strftime("%Y-%m-%d")
                    except ValueError:
                        formatted_date = "Unknown Date"

                    grouped_purchases[style_number].append({
                        "purchase_date": formatted_date,
                        "product_id": h.get("product_id"),
                        "quantity": h.get("quantity", 0),
                        "total_amount": h.get("total_amount", "$0.00"),
                        "store_location": h.get("store_location", "Unknown"),
                        "payment_method": h.get("payment_method", "Unknown")
                    })

            for style_number, purchases in grouped_purchases.items():
                total_quantity = sum(p["quantity"] for p in purchases)
                total_amount = sum(float(p["total_amount"].replace("$", "")) for p in purchases)

                product_name = next(
                    (p["name"] for p in products if str(p.get("style-number", "")) == style_number),
                    "Unknown Product"
                )

                customer_purchases.append({
                    "style_number": style_number,
                    "product_name": product_name,
                    "total_quantity": total_quantity,
                    "total_amount": f"${total_amount:.2f}",
                    "purchases": purchases
                })

            customer_info = {
                "customer_id": customer.get("customer_id", "N/A"),
                "first_name": customer.get("first_name", "N/A"),
                "last_name": customer.get("last_name", "N/A"),
                "email": customer.get("email", "N/A"),
                "phone": customer.get("phone_number", "N/A"),
                "purchase_history": customer_purchases
            }
            
            result.append(customer_info)

    return jsonify(result=result)

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('query', '').strip().lower()
    if not query:
        return jsonify([])

    try:
        customers = load_json('tory_burch_customers.json')
    except Exception as e:
        print(f"Error loading customer data: {e}")
        return jsonify([])

    if not customers:
        return jsonify([])

    matches = []
    for customer in customers:
        first_name = customer.get("first_name", "").strip().lower()
        last_name = customer.get("last_name", "").strip().lower()
        customer_id = str(customer.get("customer_id", ""))

        if query in first_name or query in last_name or query in customer_id:
            matches.append({
                "customer_id": customer_id,
                "first_name": customer.get("first_name", "N/A"),
                "last_name": customer.get("last_name", "N/A"),
                "email": customer.get("email", "N/A")
            })

    return jsonify(matches[:5])

if __name__ == "__main__":
    app.run(debug=True)
