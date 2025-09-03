import os
import sys
import json
import requests
import time
from datetime import datetime

# --- Configuration ---
LOGS_DIR = os.path.join('logs')
LOGS_DIR_BB = os.path.join(LOGS_DIR, 'best_buy')
LOGS_DIR_CP = os.path.join(LOGS_DIR, 'canada_post')
LOGS_DIR_CS = os.path.join(LOGS_DIR, 'customer_service')
CP_SHIPPING_DATA_FILE = os.path.join(LOGS_DIR_CP, 'cp_shipping_labels_data.json')
BB_HISTORY_LOG_FILE = os.path.join(LOGS_DIR_BB, 'orders_shipped_and_validated.json')
CUSTOMER_SERVICE_BB_HISTORY_LOG_FILE = os.path.join(LOGS_DIR_CS, 'orders_shipped_and_validated.json')
BEST_BUY_API_URL = 'https://marketplace.bestbuy.ca/api/orders'

from core.utils import get_best_buy_api_key

# --- Step 1: Update Tracking Numbers on Best Buy ---

def update_tracking_number(api_key, order_id, tracking_number):
    """ Updates the tracking number for a single order on Best Buy. """
    url = f"{BEST_BUY_API_URL}/{order_id}/tracking"
    headers = {'Authorization': api_key, 'Content-Type': 'application/json'}
    payload = {"carrier_code": "CPCL", "tracking_number": tracking_number}
    print(f"INFO: Updating tracking for order {order_id} with tracking number {tracking_number}...")
    try:
        response = requests.put(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"SUCCESS: Successfully updated tracking for order {order_id}.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to update tracking for order {order_id}: {e}")
        return False

def mark_order_as_shipped(api_key, order_id):
    """ Calls the Best Buy API to mark an order as shipped. """
    url = f"{BEST_BUY_API_URL}/{order_id}/ship"
    headers = {'Authorization': api_key}
    print(f"INFO: Marking order {order_id} as shipped...")
    try:
        response = requests.put(url, headers=headers)
        response.raise_for_status()
        print(f"SUCCESS: Successfully marked order {order_id} as shipped.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to mark order {order_id} as shipped: {e}")
        return False

def get_order_details(api_key, order_id):
    """ Gets the full details for a single order ID. """
    print(f"INFO: Getting full details for order {order_id}...")
    params = {'order_ids': order_id}
    headers = {'Authorization': api_key}
    try:
        response = requests.get(BEST_BUY_API_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        return data['orders'][0] if data.get('orders') else None
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Could not get order details for {order_id}: {e}")
        return None

def log_bb_history(order_details_json):
    """ Appends the full order details to the history logs. """
    if not order_details_json: return
    for log_path in [BB_HISTORY_LOG_FILE, CUSTOMER_SERVICE_BB_HISTORY_LOG_FILE]:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        log_entries = []
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                try: log_entries = json.load(f)
                except json.JSONDecodeError: log_entries = []
        log_entries.append(order_details_json)
        with open(log_path, 'w') as f:
            json.dump(log_entries, f, indent=4)
        print(f"SUCCESS: Appended order details to {log_path}")

def update_tracking_main():
    """ Main function to read shipping data and update tracking numbers. """
    print("\n--- Running Update Tracking Numbers Step ---")
    api_key = get_best_buy_api_key()
    if not api_key: return
    if not os.path.exists(CP_SHIPPING_DATA_FILE): return
    with open(CP_SHIPPING_DATA_FILE, 'r') as f:
        try: shipped_data = json.load(f)
        except json.JSONDecodeError: return
    if not shipped_data: return
    for shipment in shipped_data:
        order_id = shipment.get('order_id')
        tracking_pin = shipment.get('tracking_pin')
        if order_id and tracking_pin:
            if update_tracking_number(api_key, order_id, tracking_pin):
                if mark_order_as_shipped(api_key, order_id):
                    order_details = get_order_details(api_key, order_id)
                    log_bb_history(order_details)
    print("--- Update Tracking Numbers Step Finished ---")

# --- Step 2: Validate Shipped Status ---

def check_order_status(api_key, order_id):
    """ Checks the status of a single order on Best Buy. """
    params = {'order_ids': order_id}
    headers = {'Authorization': api_key}
    try:
        response = requests.get(BEST_BUY_API_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        return data['orders'][0].get('order_state') if data.get('orders') else None
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Could not get status for order {order_id}: {e}")
    return None

def validate_status_main():
    """ Main function to validate that orders have been marked as shipped. """
    print("\n--- Running Validate Shipped Status Step ---")
    api_key = get_best_buy_api_key()
    if not api_key: return
    if not os.path.exists(CP_SHIPPING_DATA_FILE): return
    with open(CP_SHIPPING_DATA_FILE, 'r') as f:
        try: shipped_data = json.load(f)
        except json.JSONDecodeError: return
    if not shipped_data: return
    for shipment in shipped_data:
        order_id = shipment.get('order_id')
        if order_id:
            print(f"INFO: Validating status for order {order_id}...")
            status = check_order_status(api_key, order_id)
            if status in ['SHIPPING', 'SHIPPED']:
                print(f"SUCCESS: Order {order_id} is marked as {status}.")
            else:
                print(f"WARNING: Order {order_id} has status '{status}', not 'SHIPPING' or 'SHIPPED'.")
    print("--- Validate Shipped Status Step Finished ---")

# --- Main Orchestrator ---

def main_orchestrator():
    """ Orchestrates the entire tracking number update process. """
    print("=============================================")
    print("===    PHASE 3: Update Tracking Numbers   ===")
    print("=============================================")
    print("\n>>> STEP 3.1: Updating Best Buy with tracking numbers...")
    update_tracking_main()
    print("\nINFO: Waiting for 15 seconds for API to process tracking update...")
    time.sleep(15)
    print("\n>>> STEP 3.2: Validating that order statuses are updated...")
    validate_status_main()
    print("\n=============================================")
    print("===      Phase 3 Process Has Concluded      ===")
    print("=============================================")

if __name__ == '__main__':
    main_orchestrator()
