import sys
import os
from flask import Flask, render_template, jsonify

# Ensure the core module is in the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import database-related functions if needed in the future
# from core.database import get_db_session

app = Flask(__name__)

# --- Mock Data ---
# This will be replaced with real database queries.
MOCK_WORK_ORDERS = [
    {
        "work_order_id": "ORDER-12345",
        "customer_name": "John Doe",
        "status": "pending_preparation",
        "items": [
            {"sku": "LP-HP-001", "name": "HP Elitebook 840 G5", "quantity": 1},
            {"sku": "ACC-MOUSE-01", "name": "Logitech MX Master 3", "quantity": 1},
        ]
    },
    {
        "work_order_id": "ORDER-67890",
        "customer_name": "Jane Smith",
        "status": "awaiting_scan",
        "items": [
            {"sku": "LP-DELL-002", "name": "Dell XPS 15", "quantity": 1},
        ]
    },
]

@app.route('/')
def index():
    """
    Main dashboard page.
    This will display the list of pending work orders.
    """
    # In the future, this will query the database for work orders.
    work_orders = MOCK_WORK_ORDERS
    return render_template('index.html', work_orders=work_orders)

@app.route('/api/work_order/<string:work_order_id>')
def work_order_details(work_order_id):
    """
    API endpoint to get the details of a single work order.
    """
    # In the future, this will query the database for a specific work order.
    order = next((wo for wo in MOCK_WORK_ORDERS if wo['work_order_id'] == work_order_id), None)
    if order:
        return jsonify(order)
    return jsonify({"error": "Work order not found"}), 404

@app.route('/api/verify_scan', methods=['POST'])
def verify_scan():
    """
    API endpoint to handle the barcode verification logic.
    """
    # This will receive the scanned barcodes and compare them against the DB.
    # e.g., data = request.json
    # e.g., work_order_id = data.get('work_order_id')
    # e.g., scanned_barcode = data.get('scanned_barcode')
    print("INFO: [Placeholder] Received scan verification request.")
    # For now, we'll just return a success message.
    return jsonify({"status": "success", "message": "Scan verified successfully!"})


if __name__ == '__main__':
    # Running on port 9291 as requested.
    # Host '0.0.0.0' makes it accessible on the network.
    app.run(host='0.0.0.0', port=9291, debug=True)
