
import os 
import json 
import requests

--- Configuration ---
SECRETS_FILE = os.path.join(os.path.dirname(file), '..', '..', '..', 'secrets.txt') CP_SHIPPING_DATA_FILE = os.path.join(os.path.dirname(file), '..', '..', '..', 'shipping', 'canada_post', 'cp_shipping', 'cp_shipping_labels_data.json') BEST_BUY_API_URL_BASE = 'https://marketplace.bestbuy.ca/api/orders'

def get_api_key(): """ Reads the Best Buy API key from the secrets.txt file. """ print("INFO: Reading API key from secrets.txt...") try: with open(SECRETS_FILE, 'r') as f: for line in f: if line.startswith('BEST_BUY_API_KEY='): api_key = line.strip().split('=')[1] print("SUCCESS: API key loaded.") return api_key except FileNotFoundError: print(f"ERROR: secrets.txt not found at {SECRETS_FILE}") return None

def update_tracking_number(api_key, order_id, tracking_number): """ Updates the tracking number for a single order on Best Buy. """ url = f"{BEST_BUY_API_URL_BASE}/{order_id}/tracking"

headers = {
    'Authorization': api_key,
    'Content-Type': 'application/json'
}

payload = {
    "carrier_code": "CAN_POST",
    "tracking_number": tracking_number
}

print(f"INFO: Updating tracking for order {order_id} with tracking number {tracking_number}...")
try:
    response = requests.put(url, headers=headers, json=payload)
    response.raise_for_status()
    print(f"SUCCESS: Successfully updated tracking for order {order_id}.")
    return True
except requests.exceptions.RequestException as e:
    print(f"ERROR: Failed to update tracking for order {order_id}: {e}")
    if e.response is not None:
        print("Response:", e.response.text)
    return False
def main(): """ Main function to read shipping data and update tracking numbers. """ print("\n--- Starting Update Tracking Numbers Script ---")

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
    tracking_pin = shipment.get('tracking_pin')
    
    if order_id and tracking_pin:
        update_tracking_number(api_key, order_id, tracking_pin)
    else:
        print(f"WARNING: Skipping shipment due to missing order_id or tracking_pin: {shipment}")
        
print("--- Update Tracking Numbers Script Finished ---\n")
if name == 'main': main() 
