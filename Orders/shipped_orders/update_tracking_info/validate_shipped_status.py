
import os 
import json 
import requests

--- Configuration ---
SECRETS_FILE = os.path.join(os.path.dirname(file), '..', '..', '..', 'secrets.txt') CP_SHIPPING_DATA_FILE = os.path.join(os.path.dirname(file), '..', '..', '..', 'shipping', 'canada_post', 'cp_shipping', 'cp_shipping_labels_data.json') BEST_BUY_API_URL = 'https://marketplace.bestbuy.ca/api/orders'

def get_api_key(): """ Reads the Best Buy API key from the secrets.txt file. """ print("INFO: Reading API key from secrets.txt...") try: with open(SECRETS_FILE, 'r') as f: for line in f: if line.startswith('BEST_BUY_API_KEY='): api_key = line.strip().split('=')[1] print("SUCCESS: API key loaded.") return api_key except FileNotFoundError: print(f"ERROR: secrets.txt not found at {SECRETS_FILE}") return None

def check_order_status(api_key, order_id): """ Checks the status of a single order on Best Buy. """ params = {'order_ids': order_id} headers = {'Authorization': api_key}

try:
    response = requests.get(BEST_BUY_API_URL, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    if data.get('orders'):
        return data['orders'][0].get('order_state')
except requests.exceptions.RequestException as e:
    print(f"ERROR: Could not get status for order {order_id}: {e}")
return None
def main(): """ Main function to validate that orders have been marked as shipped. """ print("\n--- Starting Validate Shipped Status Script ---")

api_key = get_api_key()
if not api_key:
    return
    
if not os.path.exists(CP_SHIPPING_DATA_FILE):
    print(f"ERROR: {CP_SHIPPING_DATA_FILE} not found.")
    return
    
with open(CP_SHIPPING_DATA_FILE, 'r') as f:
    try:
        shipped_data = json.load(f)
    except json.JSONDecodeError:
        print(f"ERROR: {CP_SHIPPING_DATA_FILE} is corrupted.")
        return
        
for shipment in shipped_data:
    order_id = shipment.get('order_id')
    if order_id:
        print(f"INFO: Validating status for order {order_id}...")
        status = check_order_status(api_key, order_id)
        if status == 'SHIPPED':
            print(f"SUCCESS: Order {order_id} is marked as SHIPPED.")
        else:
            print(f"WARNING: Order {order_id} has status '{status}', not 'SHIPPED'.")
            
print("--- Validate Shipped Status Script Finished ---\n")
if name == 'main': main() 
