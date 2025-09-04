import json
import os
from datetime import datetime

# --- Path Configuration ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
INVENTORY_FILE = os.path.join(PROJECT_ROOT, 'inventory', 'inventory.json')
COGS_LOG_FILE = os.path.join(PROJECT_ROOT, 'accounting', 'cogs_log.json')
PRODUCTS_FILE = os.path.join(PROJECT_ROOT, 'catalog', 'products.json')
SHIPPED_ORDERS_FILE = os.path.join(PROJECT_ROOT, 'Orders', 'shipped_orders', 'update_tracking_info', 'orders_shipped_and_validated.json')
PENDING_ORDERS_FILE = os.path.join(PROJECT_ROOT, 'logs', 'best_buy', 'orders_pending_shipping.json')


# Add project root to path to allow importing 'inventory'
import sys
sys.path.insert(0, PROJECT_ROOT)
from inventory import inventory as inv

def get_order_details(order_id):
    """
    Searches through order files to find the details for a given order ID.
    """
    order_files = [SHIPPED_ORDERS_FILE, PENDING_ORDERS_FILE]
    for file_path in order_files:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try:
                    orders = json.load(f)
                    for order in orders:
                        if order.get('order_id') == order_id:
                            return order
                except json.JSONDecodeError:
                    continue
    return None

def calculate_inventory_value():
    """Calculates the total value of the current inventory."""
    inventory = inv.load_inventory()
    total_value = 0
    for sku, data in inventory.items():
        total_value += data.get('quantity', 0) * data.get('cost', 0)
    return total_value

def get_inventory_value_by_category():
    """Calculates the total inventory value for each product category."""
    inventory = inv.load_inventory()
    products = []
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, 'r') as f:
            try:
                products = json.load(f)
            except json.JSONDecodeError:
                pass

    category_values = {}
    for sku, data in inventory.items():
        for product in products:
            for variant in product.get('variants', []):
                if variant.get('sku') == sku:
                    category = product.get('base_product', {}).get('series', 'Uncategorized')
                    category_values.setdefault(category, 0)
                    category_values[category] += data.get('quantity', 0) * data.get('cost', 0)
    return category_values

def record_cogs(order_id, sku, quantity):
    """Records the Cost of Goods Sold (COGS) for a fulfilled item."""
    inventory = inv.load_inventory()
    cost = inventory.get(sku, {}).get('cost', 0)
    cogs_entry = {
        'timestamp': datetime.now().isoformat(),
        'order_id': order_id,
        'sku': sku,
        'quantity': quantity,
        'cogs': cost * quantity
    }

    log_data = []
    if os.path.exists(COGS_LOG_FILE):
        with open(COGS_LOG_FILE, 'r') as f:
            try:
                log_data = json.load(f)
            except json.JSONDecodeError:
                pass # Overwrite if file is corrupt

    log_data.append(cogs_entry)

    with open(COGS_LOG_FILE, 'w') as f:
        json.dump(log_data, f, indent=2)

def calculate_profitability(order_id):
    """Calculates the profit margin for a given order."""
    order = get_order_details(order_id)
    if not order:
        return None

    total_cogs = 0
    for cogs_entry in (json.load(open(COGS_LOG_FILE)) if os.path.exists(COGS_LOG_FILE) else []):
        if cogs_entry.get('order_id') == order_id:
            total_cogs += cogs_entry.get('cogs', 0)

    sale_price = order.get('total_price', 0)
    profit = sale_price - total_cogs
    margin = (profit / sale_price) * 100 if sale_price > 0 else 0

    return {
        'order_id': order_id,
        'sale_price': sale_price,
        'cogs': total_cogs,
        'profit': profit,
        'margin_percent': margin
    }

def get_sales_by_date():
    """Gets the total sales for each day."""
    sales_by_date = {}
    if os.path.exists(SHIPPED_ORDERS_FILE):
        with open(SHIPPED_ORDERS_FILE, 'r') as f:
            try:
                orders = json.load(f)
                for order in orders:
                    date = datetime.fromisoformat(order['shipped_date'].replace('Z', '')).strftime('%Y-%m-%d')
                    sales_by_date.setdefault(date, 0)
                    sales_by_date[date] += order.get('total_price', 0)
            except (json.JSONDecodeError, KeyError):
                pass
    return sales_by_date

def get_profitability_by_product():
    """Gets the profitability for each product."""
    profitability_by_product = {}
    if os.path.exists(SHIPPED_ORDERS_FILE):
        with open(SHIPPED_ORDERS_FILE, 'r') as f:
            try:
                orders = json.load(f)
                for order in orders:
                    for line in order.get('order_lines', []):
                        sku = line.get('offer_sku')
                        profitability = calculate_profitability(order['order_id'])
                        if profitability:
                            profitability_by_product.setdefault(sku, {'total_profit': 0, 'total_margin': 0, 'count': 0})
                            profitability_by_product[sku]['total_profit'] += profitability.get('profit', 0)
                            profitability_by_product[sku]['total_margin'] += profitability.get('margin_percent', 0)
                            profitability_by_product[sku]['count'] += 1
            except (json.JSONDecodeError, KeyError):
                pass

    for sku, data in profitability_by_product.items():
        data['average_margin'] = data['total_margin'] / data['count'] if data['count'] > 0 else 0

    return profitability_by_product

if __name__ == '__main__':
    # Example usage:
    print(f"Total Inventory Value: ${calculate_inventory_value():.2f}")
    print(f"Inventory Value by Category: {get_inventory_value_by_category()}")
    print(f"Sales by date: {get_sales_by_date()}")
    print(f"Profitability by product: {get_profitability_by_product()}")

    # To test profitability, we need an order and a COGS entry.
    # First, let's create a dummy COGS entry for a test order.
    # record_cogs("TEST-ORDER-1", "FB-LPP1-G1-16-512", 1)
    # Now, let's calculate the profitability.
    # profitability = calculate_profitability("TEST-ORDER-1")
    # if profitability:
    #     print(f"Profitability for order TEST-ORDER-1: {profitability}")
