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

def get_analytics_data():
    """Fetches data for the analytics dashboard."""
    shipped_orders = []
    if os.path.exists(accounting.SHIPPED_ORDERS_FILE):
        with open(accounting.SHIPPED_ORDERS_FILE, 'r') as f:
            try:
                shipped_orders = json.load(f)
            except json.JSONDecodeError:
                pass

    gmv = sum(order.get('total_price', 0) for order in shipped_orders)

    total_profit = 0
    total_margin = 0
    for order in shipped_orders:
        profitability = accounting.calculate_profitability(order['order_id'])
        if profitability:
            total_profit += profitability.get('profit', 0)
            total_margin += profitability.get('margin_percent', 0)

    average_margin = total_margin / len(shipped_orders) if shipped_orders else 0

    sales_by_category = accounting.get_inventory_value_by_category()
    sales_by_date = accounting.get_sales_by_date()
    profitability_by_product = accounting.get_profitability_by_product()

    return {
        "gmv": gmv,
        "profitability": {
            "total_profit": total_profit,
            "average_margin": average_margin
        },
        "sales_by_category": sales_by_category,
        "sales_by_date": sales_by_date,
        "profitability_by_product": profitability_by_product
    }

@app.route('/analytics')
def analytics():
    """Displays the business analytics dashboard."""
    analytics_data = get_analytics_data()
    return render_template('analytics.html', data=analytics_data)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
