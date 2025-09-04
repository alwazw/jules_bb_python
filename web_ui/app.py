import os
import sys
from flask import Flask, render_template, request, redirect, url_for

# Add project root to path to allow importing other modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from inventory import inventory as inv
from accounting import cost as accounting

app = Flask(__name__)

@app.route('/')
def index():
    """Displays the main inventory and cost dashboard."""
    inventory_data = inv.load_inventory()
    inventory_value = accounting.calculate_inventory_value()
    return render_template('index.html', inventory=inventory_data, value=inventory_value)

@app.route('/add_stock', methods=['GET', 'POST'])
def add_stock_route():
    """Handles the page for adding new stock."""
    if request.method == 'POST':
        sku = request.form.get('sku')
        quantity = int(request.form.get('quantity', 0))
        threshold = int(request.form.get('threshold', 0))
        cost = float(request.form.get('cost', 0.0))

        if sku and quantity > 0:
            inv.add_stock(sku, quantity, threshold, cost)

        return redirect(url_for('index'))

    return render_template('add_stock.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
