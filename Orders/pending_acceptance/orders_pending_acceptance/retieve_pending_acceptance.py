
import os 
import json 
import requests

--- Configuration ---
PENDING_ACCEPTANCE_FILE = os.path.join(os.path.dirname(file), 'pending_acceptance.json') SECRETS_FILE = os.path.join(os.path.dirname(file), '..', '..', '..', 'secrets.txt') BEST_BUY_API_URL = 'https://marketplace.bestbuy.ca/api/orders'

def get_api_key(): """ Reads the Best Buy API key from the secrets.txt file. """ print("INFO: Reading API key from secrets.txt...") try: with open(SECRETS_FILE, 'r') as f: for line in f: if line.startswith('BEST_BUY_API_KEY='): api_key = line.strip().split('=')[1] print("SUCCESS: API key loaded.") return api_key except FileNotFoundError: print(f"ERROR: secrets.txt not found at {SECRETS_FILE}") return None

def retrieve_pending_orders(api_key): """ Retrieves orders with 'WAITING_ACCEPTANCE' status from the Best Buy API. """ if not api_key: print("ERROR: API key is missing. Cannot retrieve orders.") return []

headers = {
    'Authorization': api_key,
    'Content-Type': 'application/json'
}
params = {
    'order_state_codes': 'WAITING_ACCEPTANCE'
}

print("INFO: Calling Best Buy API to retrieve pending orders...")
try:
    response = requests.get(BEST_BUY_API_URL, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    print(f"SUCCESS: Found {data.get('total_count', 0)} orders from API.")
    return data.get('orders', [])
except requests.exceptions.RequestException as e:
    print(f"ERROR: API request failed: {e}")
    return []
def update_pending_acceptance_file(new_orders): """ Updates the pending_acceptance.json file with new orders, avoiding duplicates. """ print("INFO: Updating pending_acceptance.json...")

if os.path.exists(PENDING_ACCEPTANCE_FILE):
    with open(PENDING_ACCEPTANCE_FILE, 'r') as f:
        try:
            existing_orders = json.load(f)
        except json.JSONDecodeError:
            print("WARNING: pending_acceptance.json is corrupted. Starting fresh.")
            existing_orders = []
else:
    existing_orders = []
    print("INFO: pending_acceptance.json not found. A new file will be created.")

existing_order_ids = {order['order_id'] for order in existing_orders}

added_count = 0
for order in new_orders:
    if order['order_id'] not in existing_order_ids:
        existing_orders.append(order)
        existing_order_ids.add(order['order_id'])
        added_count += 1
        print(f"INFO: Added new order {order['order_id']} to pending list.")

if added_count == 0:
    print("INFO: No new pending orders to add.")
else:
    print(f"SUCCESS: Added {added_count} new orders to pending_acceptance.json.")

with open(PENDING_ACCEPTANCE_FILE, 'w') as f:
    json.dump(existing_orders, f, indent=4)
def main(): """ Main function to execute the script's logic. """ print("\n--- Starting Retrieve Pending Acceptance Script ---") api_key = get_api_key() if api_key: pending_orders = retrieve_pending_orders(api_key) if pending_orders: update_pending_acceptance_file(pending_orders) print("--- Retrieve Pending Acceptance Script Finished ---\n")

if name == 'main': main() 
EOF 

echo "SUCCESS: Created Orders/pending_acceptance/orders_pending_acceptance/retieve_pending_acceptance.py"
echo "INFO: Creating Orders/pending_acceptance/accept_orders_pending_confirmation/accept_orders.py..." 
cat > jules_bb_python/Orders/pending_acceptance/accept_orders_pending_confirmation/accept_orders.py <<'EOF' 

import os 
import json 
import requests from datetime 
import datetime

--- Configuration ---
SECRETS_FILE = os.path.join(os.path.dirname(file), '..', '..', '..', 'secrets.txt') PENDING_ACCEPTANCE_FILE = os.path.join(os.path.dirname(file), '..', 'orders_pending_acceptance', 'pending_acceptance.json') ACCEPTED_LOG_FILE = os.path.join(os.path.dirname(file), 'accepted_orders_log.json') JOURNAL_FILE = os.path.join(os.path.dirname(file), 'order_acceptance_journal.json') BEST_BUY_ACCEPT_API_URL_BASE = 'https://marketplace.bestbuy.ca/api/orders'

def get_api_key(): """ Reads the Best Buy API key from the secrets.txt file. """ print("INFO: Reading API key from secrets.txt...") try: with open(SECRETS_FILE, 'r') as f: for line in f: if line.startswith('BEST_BUY_API_KEY='): api_key = line.strip().split('=')[1] print("SUCCESS: API key loaded.") return api_key except FileNotFoundError: print(f"ERROR: secrets.txt not found at {SECRETS_FILE}") return None

def get_orders_to_accept(): """ Identifies which orders need to be accepted. """ print("INFO: Identifying orders that need to be accepted...")

if not os.path.exists(PENDING_ACCEPTANCE_FILE):
    print("ERROR: pending_acceptance.json not found. Run retrieve script first.")
    return []
with open(PENDING_ACCEPTANCE_FILE, 'r') as f:
    try:
        pending_orders = json.load(f)
    except json.JSONDecodeError:
        print("ERROR: pending_acceptance.json is corrupted.")
        return []

if os.path.exists(ACCEPTED_LOG_FILE):
    with open(ACCEPTED_LOG_FILE, 'r') as f:
        try:
            accepted_orders_log = json.load(f)
        except json.JSONDecodeError:
            print("WARNING: accepted_orders_log.json is corrupted. Starting fresh.")
            accepted_orders_log = []
else:
    accepted_orders_log = []
    print("INFO: accepted_orders_log.json not found. A new file will be created.")

accepted_order_ids = {entry['order_id'] for entry in accepted_orders_log}

orders_to_accept = [order for order in pending_orders if order['order_id'] not in accepted_order_ids]

if not orders_to_accept:
    print("INFO: No new orders to accept.")
else:
    print(f"INFO: Found {len(orders_to_accept)} orders to be accepted.")
    
return orders_to_accept
def accept_order(api_key, order): """ Calls the Best Buy API to accept a single order. """ if not api_key: print("ERROR: API key is missing. Cannot accept order.") return None

order_id = order['order_id']

url = f"{BEST_BUY_ACCEPT_API_URL_BASE}/{order_id}/accept"

headers = {
    'Authorization': api_key,
    'Content-Type': 'application/json'
}

order_lines_payload = []
for line in order.get('order_lines', []):
    order_lines_payload.append({
        "accepted": True,
        "id": line['order_line_id']
    })

payload = {
    "order_lines": order_lines_payload
}

print(f"INFO: Sending API request to accept order {order_id} at {url}...")
print(f"INFO: Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.put(url, headers=headers, json=payload)
    response.raise_for_status()
    print(f"SUCCESS: API call for order {order_id} was successful with status code {response.status_code}.")
    if response.content:
        return response.json()
    return {"status": "success", "message": "Order accepted successfully."}
except requests.exceptions.RequestException as e:
    print(f"ERROR: API request to accept order {order_id} failed: {e}")
    if e.response is not None:
        return e.response.json()
    return {"error": str(e)}
def log_acceptance(order_id, api_response): """ Logs the acceptance in the log and journal files. """ timestamp = datetime.now().isoformat()

print(f"INFO: Logging acceptance for order {order_id} in accepted_orders_log.json...")
if os.path.exists(ACCEPTED_LOG_FILE):
    with open(ACCEPTED_LOG_FILE, 'r') as f:
        try:
            log_data = json.load(f)
        except json.JSONDecodeError:
            log_data = []
else:
    log_data = []

log_data.append({"order_id": order_id, "timestamp": timestamp})

with open(ACCEPTED_LOG_FILE, 'w') as f:
    json.dump(log_data, f, indent=4)

print(f"INFO: Logging API response for order {order_id} in order_acceptance_journal.json...")
if os.path.exists(JOURNAL_FILE):
    with open(JOURNAL_FILE, 'r') as f:
        try:
            journal_data = json.load(f)
        except json.JSONDecodeError:
            journal_data = []
else:
    journal_data = []
    
journal_data.append({
    "order_id": order_id,
    "timestamp": timestamp,
    "api_response": api_response
})

with open(JOURNAL_FILE, 'w') as f:
    json.dump(journal_data, f, indent=4)
def main(): """ Main function to execute the script's logic. """ print("\n--- Starting Accept Orders Script ---") api_key = get_api_key() if api_key: orders_to_process = get_orders_to_accept() for order in orders_to_process: api_response = accept_order(api_key, order) if api_response: log_acceptance(order['order_id'], api_response) print("--- Accept Orders Script Finished ---\n")

if name == 'main': main() 
EOF 

echo "SUCCESS: Created Orders/pending_acceptance/accept_orders_pending_confirmation/accept_orders.py"
echo "INFO: Creating Orders/pending_acceptance/accept_pending_orders_validation/order_acceptance_validation.py..." 

cat > jules_bb_python/Orders/pending_acceptance/accept_pending_orders_validation/order_acceptance_validation.py <<'EOF' 

import os 
import json 
import requests from datetime 
import datetime

--- Configuration ---
SECRETS_FILE = os.path.join(os.path.dirname(file), '..', '..', '..', 'secrets.txt') ACCEPTED_LOG_FILE = os.path.join(os.path.dirname(file), '..', 'accept_orders_pending_confirmation', 'accepted_orders_log.json') FAILED_LOG_FILE = os.path.join(os.path.dirname(file), 'failed_order_acceptances.json') BEST_BUY_API_URL = 'https://marketplace.bestbuy.ca/api/orders'

def get_api_key(): """ Reads the Best Buy API key from the secrets.txt file. """ print("INFO: Reading API key from secrets.txt...") try: with open(SECRETS_FILE, 'r') as f: for line in f: if line.startswith('BEST_BUY_API_KEY='): api_key = line.strip().split('=')[1] print("SUCCESS: API key loaded.") return api_key except FileNotFoundError: print(f"ERROR: secrets.txt not found at {SECRETS_FILE}") return None

def get_currently_pending_orders(api_key): """ Retrieves a fresh list of orders with 'WAITING_ACCEPTANCE' status from the Best Buy API. """ if not api_key: print("ERROR: API key is missing. Cannot retrieve orders.") return []

headers = {'Authorization': api_key}
params = {'order_state_codes': 'WAITING_ACCEPTANCE'}

print("INFO: Calling Best Buy API for a fresh list of pending orders for validation...")
try:
    response = requests.get(BEST_BUY_API_URL, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    print(f"SUCCESS: API reports {data.get('total_count', 0)} orders are currently pending acceptance.")
    return data.get('orders', [])
except requests.exceptions.RequestException as e:
    print(f"ERROR: API request failed during validation: {e}")
    return []
def validate_acceptance(): """ Compares recently accepted orders with the current pending list to validate acceptance. """ print("INFO: Starting order acceptance validation...") api_key = get_api_key() if not api_key: return 'ERROR'

currently_pending_orders_list = get_currently_pending_orders(api_key)
currently_pending_ids = {order['order_id'] for order in currently_pending_orders_list}

if not os.path.exists(ACCEPTED_LOG_FILE):
    print("ERROR: accepted_orders_log.json not found. Cannot perform validation.")
    return 'ERROR'
with open(ACCEPTED_LOG_FILE, 'r') as f:
    try:
        accepted_log = json.load(f)
    except json.JSONDecodeError:
        print("ERROR: accepted_orders_log.json is corrupted.")
        return 'ERROR'
        
accepted_log_ids = {entry['order_id'] for entry in accepted_log}

failed_acceptances = currently_pending_ids.intersection(accepted_log_ids)

if failed_acceptances:
    print(f"ERROR: Found {len(failed_acceptances)} orders that failed to be accepted.")
    print("Failed Order Numbers:", list(failed_acceptances))
    
    failed_log_entries = []
    if os.path.exists(FAILED_LOG_FILE):
        with open(FAILED_LOG_FILE, 'r') as f:
            try:
                failed_log_entries = json.load(f)
            except json.JSONDecodeError:
                pass
                
    for order_id in failed_acceptances:
        failed_log_entries.append({
            "order_id": order_id,
            "failure_timestamp": datetime.now().isoformat()
        })
        
    with open(FAILED_LOG_FILE, 'w') as f:
        json.dump(failed_log_entries, f, indent=4)
    
    return 'VALIDATION_FAILED'

new_unprocessed_orders = currently_pending_ids.difference(accepted_log_ids)

if new_unprocessed_orders:
    print(f"INFO: Found {len(new_unprocessed_orders)} new pending orders that were not in the last run.")
    print("New Order Numbers:", list(new_unprocessed_orders))
    return 'NEW_ORDERS_FOUND'
    
if not currently_pending_ids:
    print("SUCCESS: All orders have been successfully accepted.")
    return 'SUCCESS'
    
print("INFO: Validation finished. Some orders may still be pending that were not processed in this run.")
return 'INCOMPLETE'
def main(): """ Main function to execute the script's logic. """ print("\n--- Starting Order Acceptance Validation Script ---") validation_status = validate_acceptance() print(f"Validation Result: {validation_status}") print("--- Order Acceptance Validation Script Finished ---\n")

if name == 'main': main() 
