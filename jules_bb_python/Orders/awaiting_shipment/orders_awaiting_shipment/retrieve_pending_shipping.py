
import os 
import json 
import requests

--- Configuration ---
SECRETS_FILE = os.path.join(os.path.dirname(file), '..', '..', '..', 'secrets.txt') PENDING_SHIPPING_FILE = os.path.join(os.path.dirname(file), 'orders_pending_shipping.json') BEST_BUY_API_URL = 'https://marketplace.bestbuy.ca/api/orders'

def get_api_key(): """ Reads the Best Buy API key from the secrets.txt file. """ print("INFO: Reading API key from secrets.txt...") try: with open(SECRETS_FILE, 'r') as f: for line in f: if line.startswith('BEST_BUY_API_KEY='): api_key = line.strip().split('=')[1] print("SUCCESS: API key loaded.") return api_key except FileNotFoundError: print(f"ERROR: secrets.txt not found at {SECRETS_FILE}") return None

def retrieve_awaiting_shipment_orders(api_key): """ Retrieves orders with 'SHIPPING' status from the Best Buy API. """ if not api_key: print("ERROR: API key is missing. Cannot retrieve orders.") return []

headers = {
    'Authorization': api_key,
    'Content-Type': 'application/json'
}
params = {
    'order_state_codes': 'SHIPPING'
}

print("INFO: Calling Best Buy API to retrieve orders awaiting shipment...")
try:
    response = requests.get(BEST_BUY_API_URL, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    print(f"SUCCESS: Found {data.get('total_count', 0)} orders awaiting shipment from API.")
    return data.get('orders', [])
except requests.exceptions.RequestException as e:
    print(f"ERROR: API request failed: {e}")
    return []
def update_pending_shipping_file(new_orders): """ Updates the orders_pending_shipping.json file with new orders, avoiding duplicates. """ print("INFO: Updating orders_pending_shipping.json...")

if os.path.exists(PENDING_SHIPPING_FILE):
    with open(PENDING_SHIPPING_FILE, 'r') as f:
        try:
            existing_orders = json.load(f)
        except json.JSONDecodeError:
            print("WARNING: orders_pending_shipping.json is corrupted. Starting fresh.")
            existing_orders = []
else:
    existing_orders = []
    print("INFO: orders_pending_shipping.json not found. A new file will be created.")

existing_order_ids = {order['order_id'] for order in existing_orders}

added_count = 0
for order in new_orders:
    if order['order_id'] not in existing_order_ids:
        existing_orders.append(order)
        existing_order_ids.add(order['order_id'])
        added_count += 1
        print(f"INFO: Added new order {order['order_id']} to pending shipping list.")

if added_count == 0:
    print("INFO: No new orders awaiting shipment to add.")
else:
    print(f"SUCCESS: Added {added_count} new orders to orders_pending_shipping.json.")

with open(PENDING_SHIPPING_FILE, 'w') as f:
    json.dump(existing_orders, f, indent=4)
def main(): """ Main function to execute the script's logic. """ print("\n--- Starting Retrieve Orders Pending Shipment Script ---") api_key = get_api_key() if api_key: awaiting_shipment_orders = retrieve_awaiting_shipment_orders(api_key) if awaiting_shipment_orders: update_pending_shipping_file(awaiting_shipment_orders) print("--- Retrieve Orders Pending Shipment Script Finished ---\n")

if name == 'main': main() 
