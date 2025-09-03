import os
import json
import requests
import time
from datetime import datetime

# It's better to have a single, well-defined way to get the root directory.
# Assuming the script is run from the project root, or we can use a more robust method.
# For now, let's define paths relative to the project root.
LOGS_DIR = os.path.join('logs', 'best_buy')
PENDING_ACCEPTANCE_FILE = os.path.join(LOGS_DIR, 'pending_acceptance.json')
ACCEPTED_LOG_FILE = os.path.join(LOGS_DIR, 'accepted_orders_log.json')
FAILED_LOG_FILE = os.path.join(LOGS_DIR, 'failed_order_acceptances.json')
JOURNAL_FILE = os.path.join(LOGS_DIR, 'order_acceptance_journal.json')
BEST_BUY_API_URL = 'https://marketplace.bestbuy.ca/api/orders'

from core.utils import get_best_buy_api_key

# --- Functions from retieve_pending_acceptance.py ---

def retrieve_pending_orders(api_key):
    """ Retrieves orders with 'WAITING_ACCEPTANCE' status from the Best Buy API. """
    if not api_key:
        print("ERROR: API key is missing. Cannot retrieve orders.")
        return []

    headers = {'Authorization': api_key, 'Content-Type': 'application/json'}
    params = {'order_state_codes': 'WAITING_ACCEPTANCE'}

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

def update_pending_acceptance_file(new_orders):
    """ Updates the pending_acceptance.json file with new orders, avoiding duplicates. """
    os.makedirs(LOGS_DIR, exist_ok=True)
    print(f"INFO: Updating {PENDING_ACCEPTANCE_FILE}...")

    existing_orders = []
    if os.path.exists(PENDING_ACCEPTANCE_FILE):
        with open(PENDING_ACCEPTANCE_FILE, 'r') as f:
            try:
                existing_orders = json.load(f)
            except json.JSONDecodeError:
                print("WARNING: pending_acceptance.json is corrupted. Starting fresh.")
                existing_orders = []
    else:
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

    with open(PENDING_ACCEPTANCE_FILE, 'w') as f:
        json.dump(existing_orders, f, indent=4)

    if added_count > 0:
        print(f"SUCCESS: Added {added_count} new orders to pending_acceptance.json.")

def retrieve_main():
    """ Main function for retrieving pending orders. """
    print("\n--- Running Retrieve Pending Acceptance Step ---")
    api_key = get_best_buy_api_key()
    if api_key:
        pending_orders = retrieve_pending_orders(api_key)
        update_pending_acceptance_file(pending_orders)
    print("--- Retrieve Pending Acceptance Step Finished ---")

# --- Functions from accept_orders.py ---

def get_orders_to_accept():
    """ Identifies which orders need to be accepted. """
    print("INFO: Identifying orders that need to be accepted...")
    if not os.path.exists(PENDING_ACCEPTANCE_FILE):
        print("INFO: pending_acceptance.json not found. Assuming no orders to process.")
        return []
    with open(PENDING_ACCEPTANCE_FILE, 'r') as f:
        try:
            pending_orders = json.load(f)
        except json.JSONDecodeError:
            print("ERROR: pending_acceptance.json is corrupted.")
            return []

    if not pending_orders:
        print("INFO: pending_acceptance.json is empty. No orders to process.")
        return []

    accepted_orders_log = []
    if os.path.exists(ACCEPTED_LOG_FILE):
        with open(ACCEPTED_LOG_FILE, 'r') as f:
            try:
                accepted_orders_log = json.load(f)
            except json.JSONDecodeError:
                print("WARNING: accepted_orders_log.json is corrupted. Starting fresh.")
                accepted_orders_log = []
    else:
        print("INFO: accepted_orders_log.json not found. A new file will be created.")

    accepted_order_ids = {entry['order_id'] for entry in accepted_orders_log}
    orders_to_accept = [order for order in pending_orders if order['order_id'] not in accepted_order_ids]

    if not orders_to_accept:
        print("INFO: No new orders to accept.")
    else:
        print(f"INFO: Found {len(orders_to_accept)} orders to be accepted.")
    return orders_to_accept

def accept_order(api_key, order):
    """ Calls the Best Buy API to accept a single order. """
    if not api_key:
        print("ERROR: API key is missing. Cannot accept order.")
        return None
    order_id = order['order_id']
    url = f"{BEST_BUY_API_URL}/{order_id}/accept"
    headers = {'Authorization': api_key, 'Content-Type': 'application/json'}
    order_lines_payload = [{"accepted": True, "id": line['order_line_id']} for line in order.get('order_lines', [])]
    payload = {"order_lines": order_lines_payload}

    print(f"INFO: Sending API request to accept order {order_id}...")
    try:
        response = requests.put(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"SUCCESS: API call for order {order_id} was successful.")
        if response.content:
            return response.json()
        return {"status": "success", "message": "Order accepted successfully."}
    except requests.exceptions.RequestException as e:
        print(f"ERROR: API request to accept order {order_id} failed: {e}")
        return e.response.json() if e.response else {"error": str(e)}

def log_acceptance(order_id, api_response):
    """ Logs the acceptance in the log and journal files. """
    os.makedirs(LOGS_DIR, exist_ok=True)
    timestamp = datetime.now().isoformat()
    print(f"INFO: Logging acceptance for order {order_id}...")

    log_data = []
    if os.path.exists(ACCEPTED_LOG_FILE):
        with open(ACCEPTED_LOG_FILE, 'r') as f:
            try:
                log_data = json.load(f)
            except json.JSONDecodeError:
                log_data = []
    log_data.append({"order_id": order_id, "timestamp": timestamp})
    with open(ACCEPTED_LOG_FILE, 'w') as f:
        json.dump(log_data, f, indent=4)

    journal_data = []
    if os.path.exists(JOURNAL_FILE):
        with open(JOURNAL_FILE, 'r') as f:
            try:
                journal_data = json.load(f)
            except json.JSONDecodeError:
                journal_data = []
    journal_data.append({"order_id": order_id, "timestamp": timestamp, "api_response": api_response})
    with open(JOURNAL_FILE, 'w') as f:
        json.dump(journal_data, f, indent=4)

def accept_main():
    """ Main function for accepting orders. """
    print("\n--- Running Accept Orders Step ---")
    api_key = get_best_buy_api_key()
    if api_key:
        orders_to_process = get_orders_to_accept()
        for order in orders_to_process:
            api_response = accept_order(api_key, order)
            if api_response:
                log_acceptance(order['order_id'], api_response)
    print("--- Accept Orders Step Finished ---")

# --- Functions from order_acceptance_validation.py ---

def get_currently_pending_orders(api_key):
    """ Retrieves a fresh list of orders with 'WAITING_ACCEPTANCE' status from the Best Buy API. """
    if not api_key:
        print("ERROR: API key is missing.")
        return []
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

def validate_acceptance():
    """ Compares recently accepted orders with the current pending list to validate acceptance. """
    print("\n--- Running Order Acceptance Validation Step ---")
    api_key = get_best_buy_api_key()
    if not api_key: return 'ERROR'

    currently_pending_orders_list = get_currently_pending_orders(api_key)
    currently_pending_ids = {order['order_id'] for order in currently_pending_orders_list}

    accepted_log = []
    if os.path.exists(ACCEPTED_LOG_FILE):
        with open(ACCEPTED_LOG_FILE, 'r') as f:
            try:
                accepted_log = json.load(f)
            except json.JSONDecodeError:
                print("ERROR: accepted_orders_log.json is corrupted.")
                return 'ERROR'

    accepted_log_ids = {entry['order_id'] for entry in accepted_log}
    failed_acceptances = currently_pending_ids.intersection(accepted_log_ids)

    if failed_acceptances:
        print(f"ERROR: Found {len(failed_acceptances)} orders that failed to be accepted: {list(failed_acceptances)}")
        failed_log_entries = []
        if os.path.exists(FAILED_LOG_FILE):
            with open(FAILED_LOG_FILE, 'r') as f:
                try:
                    failed_log_entries = json.load(f)
                except json.JSONDecodeError: pass
        for order_id in failed_acceptances:
            failed_log_entries.append({"order_id": order_id, "failure_timestamp": datetime.now().isoformat()})
        with open(FAILED_LOG_FILE, 'w') as f:
            json.dump(failed_log_entries, f, indent=4)
        return 'VALIDATION_FAILED'

    new_unprocessed_orders = currently_pending_ids.difference(accepted_log_ids)
    if new_unprocessed_orders:
        print(f"INFO: Found {len(new_unprocessed_orders)} new pending orders that were not in the last run: {list(new_unprocessed_orders)}")
        return 'NEW_ORDERS_FOUND'

    if not currently_pending_ids:
        print("SUCCESS: All orders have been successfully accepted.")
        return 'SUCCESS'

    print("INFO: Validation finished. Some orders may still be pending that were not processed in this run.")
    return 'INCOMPLETE'

# --- Main Orchestrator ---

def main_orchestrator():
    """ Orchestrates the entire order acceptance process flow. """
    print("=============================================")
    print("===      PHASE 1: Order Acceptance        ===")
    print("=============================================")
    max_retries = 3
    for i in range(max_retries):
        print(f"\n>>> Main Loop Attempt: {i + 1}/{max_retries} <<<")

        print("\n>>> STEP 1.1: Retrieving all orders pending acceptance...")
        retrieve_main()

        print("\n>>> STEP 1.2: Sending requests to accept new orders...")
        accept_main()

        print("\nINFO: Waiting for 5 seconds for API to process acceptances...")
        time.sleep(5)

        print("\n>>> STEP 1.3: Validating that orders were accepted...")
        validation_status = validate_acceptance()

        print(f"\n>>> FINAL VALIDATION STATUS FOR PHASE 1: {validation_status} <<<")

        if validation_status == 'SUCCESS':
            print("\n✅ Graceful termination of Phase 1: All orders processed successfully.")
            break
        elif validation_status == 'VALIDATION_FAILED':
            print("\n❌ Error in Phase 1: Some orders failed to be accepted. Check 'failed_order_acceptances.json'.")
            break
        elif validation_status == 'NEW_ORDERS_FOUND':
            print("\n🔄 New orders found. Looping back to the start.")
            if (i + 1) >= max_retries:
                print("\n❌ Error: Reached max retries for Phase 1. Exiting to avoid infinite loop.")
        else:
            print("\n- Phase 1 finished, but some pending orders may remain. Please check the logs.")
            break
        print("---------------------------------------------")
        time.sleep(2)

    print("\n=============================================")
    print("===      Phase 1 Process Has Concluded      ===")
    print("=============================================")

if __name__ == '__main__':
    main_orchestrator()
