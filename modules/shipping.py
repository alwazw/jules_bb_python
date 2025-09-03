import os
import sys
import json
import requests
import base64
import time
import xml.etree.ElementTree as ET
from xml.dom import minidom

# --- Configuration ---
LOGS_DIR = os.path.join('logs')
LOGS_DIR_BB = os.path.join(LOGS_DIR, 'best_buy')
LOGS_DIR_CP = os.path.join(LOGS_DIR, 'canada_post')
PENDING_SHIPPING_FILE = os.path.join(LOGS_DIR_BB, 'orders_pending_shipping.json')
XML_OUTPUT_DIR = os.path.join(LOGS_DIR_CP, 'create_label_xml_files')
PDF_OUTPUT_DIR = os.path.join(LOGS_DIR_CP, 'cp_pdf_shipping_labels')
CP_SHIPPING_DATA_FILE = os.path.join(LOGS_DIR_CP, 'cp_shipping_labels_data.json')
CP_HISTORY_LOG_FILE = os.path.join(LOGS_DIR_CP, 'cp_shipping_history_log.json')
CUSTOMER_SERVICE_CP_HISTORY_LOG_FILE = os.path.join(LOGS_DIR, 'customer_service', 'cp_shipping_history_log.json')

BEST_BUY_API_URL = 'https://marketplace.bestbuy.ca/api/orders'

SENDER_NAME = "VISIONVATION INC."
SENDER_COMPANY = "VISIONVATION INC."
SENDER_CONTACT_PHONE = "647-444-0848"
SENDER_ADDRESS = "133 Rock Fern Way"
SENDER_CITY = "North York"
SENDER_PROVINCE = "ON"
SENDER_POSTAL_CODE = "M2J 4N3"
SENDER_COUNTRY = "CA"


from core.utils import get_best_buy_api_key, get_canada_post_credentials

# --- Step 1: Retrieve Shippable Orders ---

def retrieve_awaiting_shipment_orders(api_key):
    if not api_key: return []
    headers = {'Authorization': api_key, 'Content-Type': 'application/json'}
    params = {'order_state_codes': 'SHIPPING'}
    print("INFO: Calling Best Buy API to retrieve orders awaiting shipment...")
    try:
        response = requests.get(BEST_BUY_API_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        print(f"SUCCESS: Found {data.get('total_count', 0)} orders awaiting shipment.")
        return data.get('orders', [])
    except requests.exceptions.RequestException as e:
        print(f"ERROR: API request failed: {e}")
        return []

def update_pending_shipping_file(new_orders):
    os.makedirs(LOGS_DIR_BB, exist_ok=True)
    existing_orders = []
    if os.path.exists(PENDING_SHIPPING_FILE):
        with open(PENDING_SHIPPING_FILE, 'r') as f:
            try: existing_orders = json.load(f)
            except json.JSONDecodeError: pass
    existing_order_ids = {order['order_id'] for order in existing_orders}
    added_count = 0
    for order in new_orders:
        if order['order_id'] not in existing_order_ids:
            existing_orders.append(order)
            existing_order_ids.add(order['order_id'])
            added_count += 1
    if added_count > 0:
        with open(PENDING_SHIPPING_FILE, 'w') as f:
            json.dump(existing_orders, f, indent=4)
        print(f"SUCCESS: Added {added_count} new orders to orders_pending_shipping.json.")
    else:
        print("INFO: No new orders awaiting shipment to add.")

def retrieve_shipping_main():
    print("\n--- Running Retrieve Orders Pending Shipment Step ---")
    api_key = get_best_buy_api_key()
    if api_key:
        awaiting_shipment_orders = retrieve_awaiting_shipment_orders(api_key)
        update_pending_shipping_file(awaiting_shipment_orders)
    print("--- Retrieve Orders Pending Shipment Step Finished ---")

# --- Step 2: Transform Data and Create Labels ---

def create_xml_payload(order, contract_id, paid_by_customer):
    order_id = order['order_id']
    customer = order['customer']
    shipping = customer['shipping_address']
    offer_sku = order['order_lines'][0]['offer_sku']
    quantity = order['order_lines'][0]['quantity']
    shipment = ET.Element('shipment', xmlns="http://www.canadapost.ca/ws/shipment-v8")
    ET.SubElement(shipment, 'transmit-shipment').text = 'true'
    ET.SubElement(shipment, 'requested-shipping-point').text = SENDER_POSTAL_CODE.replace(" ", "")
    delivery_spec = ET.SubElement(shipment, 'delivery-spec')
    ET.SubElement(delivery_spec, 'service-code').text = 'DOM.EP'
    sender = ET.SubElement(delivery_spec, 'sender')
    ET.SubElement(sender, 'name').text = SENDER_NAME
    ET.SubElement(sender, 'company').text = SENDER_COMPANY
    ET.SubElement(sender, 'contact-phone').text = SENDER_CONTACT_PHONE
    sender_address_details = ET.SubElement(sender, 'address-details')
    ET.SubElement(sender_address_details, 'address-line-1').text = SENDER_ADDRESS
    ET.SubElement(sender_address_details, 'city').text = SENDER_CITY
    ET.SubElement(sender_address_details, 'prov-state').text = SENDER_PROVINCE
    ET.SubElement(sender_address_details, 'country-code').text = SENDER_COUNTRY
    ET.SubElement(sender_address_details, 'postal-zip-code').text = SENDER_POSTAL_CODE
    destination = ET.SubElement(delivery_spec, 'destination')
    ET.SubElement(destination, 'name').text = f"{customer['firstname']} {customer['lastname']}"
    ET.SubElement(destination, 'company').text = f"{quantity}x {offer_sku}"
    dest_address_details = ET.SubElement(destination, 'address-details')
    ET.SubElement(dest_address_details, 'address-line-1').text = shipping['street_1']
    ET.SubElement(dest_address_details, 'city').text = shipping['city']
    ET.SubElement(dest_address_details, 'prov-state').text = shipping['state']
    ET.SubElement(dest_address_details, 'country-code').text = 'CA'
    ET.SubElement(dest_address_details, 'postal-zip-code').text = shipping['zip_code']
    parcel_characteristics = ET.SubElement(delivery_spec, 'parcel-characteristics')
    ET.SubElement(parcel_characteristics, 'weight').text = '1.8'
    ET.SubElement(delivery_spec, 'print-preferences')
    references = ET.SubElement(delivery_spec, 'references')
    ET.SubElement(references, 'customer-ref-1').text = order_id
    settlement_info = ET.SubElement(delivery_spec, 'settlement-info')
    ET.SubElement(settlement_info, 'paid-by-customer').text = paid_by_customer
    ET.SubElement(settlement_info, 'contract-id').text = contract_id
    xml_str = ET.tostring(shipment, 'utf-8')
    dom = minidom.parseString(xml_str)
    return dom.toprettyxml(indent="  ")

def transform_data_main():
    print("\n--- Running Transform Shipping Data to XML Step ---")
    _, _, _, paid_by_customer, contract_id = get_canada_post_credentials()
    if not all([paid_by_customer, contract_id]): return
    os.makedirs(XML_OUTPUT_DIR, exist_ok=True)
    if not os.path.exists(PENDING_SHIPPING_FILE): return
    with open(PENDING_SHIPPING_FILE, 'r') as f:
        try: orders = json.load(f)
        except json.JSONDecodeError: return
    if not orders: return
    for order in orders:
        order_id = order['order_id']
        xml_content = create_xml_payload(order, contract_id, paid_by_customer)
        xml_filename = os.path.join(XML_OUTPUT_DIR, f"{order_id}.xml")
        with open(xml_filename, 'w') as xml_file:
            xml_file.write(xml_content)
        print(f"SUCCESS: Created XML file for order {order_id}")
    print("--- Transform Shipping Data to XML Step Finished ---")


# --- Step 3: Create CP Labels and Validate ---

def log_shipping_data(order_id, tracking_pin, label_url, api_response_text):
    os.makedirs(os.path.dirname(CP_SHIPPING_DATA_FILE), exist_ok=True)
    log_entries = []
    if os.path.exists(CP_SHIPPING_DATA_FILE):
        with open(CP_SHIPPING_DATA_FILE, 'r') as f:
            try: log_entries = json.load(f)
            except json.JSONDecodeError: pass
    log_entries.append({"order_id": order_id, "tracking_pin": tracking_pin, "label_url": label_url, "timestamp": datetime.now().isoformat(), "api_response": api_response_text})
    with open(CP_SHIPPING_DATA_FILE, 'w') as f:
        json.dump(log_entries, f, indent=4)

def log_cp_history(shipment_details_xml):
    if not shipment_details_xml: return
    for log_path in [CP_HISTORY_LOG_FILE, CUSTOMER_SERVICE_CP_HISTORY_LOG_FILE]:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        log_entries = []
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                try: log_entries = json.load(f)
                except json.JSONDecodeError: log_entries = []
        log_entries.append({"timestamp": datetime.now().isoformat(), "shipment_details": shipment_details_xml})
        with open(log_path, 'w') as f:
            json.dump(log_entries, f, indent=4)

def create_shipment_and_get_label(api_user, api_password, customer_number, xml_content, order_id):
    auth_string = f"{api_user}:{api_password}"
    auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    cp_api_url = f'https://soa-gw.canadapost.ca/rs/{customer_number}/{customer_number}/shipment'
    headers = {'Authorization': f'Basic {auth_b64}', 'Content-Type': 'application/vnd.cpc.shipment-v8+xml', 'Accept': 'application/vnd.cpc.shipment-v8+xml'}
    print(f"INFO: Sending request to Canada Post 'Create Shipment' API for order {order_id}...")
    try:
        response = requests.post(cp_api_url, headers=headers, data=xml_content)
        response.raise_for_status()
        response_text = response.text
        root = ET.fromstring(response_text)
        label_url = root.find(".//{http://www.canadapost.ca/ws/shipment-v8}link[@rel='label']").get('href')
        tracking_pin = root.find(".//{http://www.canadapost.ca/ws/shipment-v8}tracking-pin").text
        details_url = root.find(".//{http://www.canadapost.ca/ws/shipment-v8}link[@rel='details']").get('href')
        log_shipping_data(order_id, tracking_pin, label_url, response_text)
        return label_url, details_url, tracking_pin
    except (requests.exceptions.RequestException, ET.ParseError) as e:
        print(f"ERROR: 'Create Shipment' API request failed for order {order_id}: {e}")
        log_shipping_data(order_id, None, None, e.response.text if hasattr(e, 'response') else str(e))
        return None, None, None

def download_label(label_url, api_user, api_password, output_path):
    if not label_url: return
    auth_string = f"{api_user}:{api_password}"
    auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    headers = {'Accept': 'application/pdf', 'Authorization': f'Basic {auth_b64}'}
    print(f"INFO: Downloading label from {label_url}...")
    try:
        response = requests.get(label_url, headers=headers)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"SUCCESS: Saved label to {output_path}")
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to download label: {e}")

def get_shipment_details(api_user, api_password, shipment_details_url):
    if not shipment_details_url: return None
    auth_string = f"{api_user}:{api_password}"
    auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    headers = {'Accept': 'application/vnd.cpc.shipment-v8+xml', 'Authorization': f'Basic {auth_b64}'}
    try:
        response = requests.get(shipment_details_url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException:
        return None

def get_tracking_summary(api_user, api_password, tracking_pin):
    if not tracking_pin: return False
    tracking_url = f"https://soa-gw.canadapost.ca/vis/track/pin/{tracking_pin}/summary"
    auth_string = f"{api_user}:{api_password}"
    auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    headers = {'Accept': 'application/vnd.cpc.track-v2+xml', 'Authorization': f'Basic {auth_b64}'}
    print(f"INFO: Validating tracking PIN {tracking_pin}...")
    try:
        response = requests.get(tracking_url, headers=headers)
        response.raise_for_status()
        print(f"SUCCESS: Tracking PIN {tracking_pin} is valid.")
        return True
    except requests.exceptions.RequestException:
        print(f"CRITICAL: Tracking PIN {tracking_pin} could not be validated.")
        return False

def create_labels_main():
    print("\n--- Running Create PDF Labels Step ---")
    os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)
    api_user, api_password, customer_number, _, _ = get_canada_post_credentials()
    if not all([api_user, api_password, customer_number]): return
    if not os.path.exists(XML_OUTPUT_DIR): return
    xml_files = [f for f in os.listdir(XML_OUTPUT_DIR) if f.endswith('.xml')]
    if not xml_files: return
    for xml_file in xml_files:
        order_id = os.path.splitext(xml_file)[0]
        xml_path = os.path.join(XML_OUTPUT_DIR, xml_file)
        with open(xml_path, 'r') as f:
            xml_content = f.read()
        label_url, details_url, tracking_pin = create_shipment_and_get_label(api_user, api_password, customer_number, xml_content, order_id)
        if details_url:
            shipment_details_xml = get_shipment_details(api_user, api_password, details_url)
            log_cp_history(shipment_details_xml)
        if tracking_pin:
            time.sleep(30)
            get_tracking_summary(api_user, api_password, tracking_pin)
        if label_url:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            pdf_path = os.path.join(PDF_OUTPUT_DIR, f"{order_id}_{timestamp}.pdf")
            download_label(label_url, api_user, api_password, pdf_path)
    print("--- Create PDF Labels Step Finished ---")


# --- Step 4: Clear Shipped Orders from Pending List ---

def clear_shipped_orders_main():
    print("\n--- Running Clear Shipped Orders Step ---")
    if not os.path.exists(CP_SHIPPING_DATA_FILE): return
    with open(CP_SHIPPING_DATA_FILE, 'r') as f:
        try: shipped_data = json.load(f)
        except json.JSONDecodeError: return
    if not os.path.exists(PENDING_SHIPPING_FILE): return
    with open(PENDING_SHIPPING_FILE, 'r') as f:
        try: pending_orders = json.load(f)
        except json.JSONDecodeError: return
    shipped_order_ids = {entry['order_id'] for entry in shipped_data if entry.get('tracking_pin')}
    remaining_pending_orders = [order for order in pending_orders if order['order_id'] not in shipped_order_ids]
    if len(remaining_pending_orders) < len(pending_orders):
        with open(PENDING_SHIPPING_FILE, 'w') as f:
            json.dump(remaining_pending_orders, f, indent=4)
        print("SUCCESS: orders_pending_shipping.json has been updated.")
    else:
        print("INFO: No orders to remove from the pending list.")
    print("--- Clear Shipped Orders Step Finished ---")


# --- Main Orchestrator ---

def has_label_been_created(order_id):
    if not os.path.exists(CP_HISTORY_LOG_FILE): return False
    with open(CP_HISTORY_LOG_FILE, 'r') as f:
        try:
            history = json.load(f)
            for entry in history:
                if order_id in entry.get("shipment_details", ""): return True
        except (json.JSONDecodeError, TypeError): return False
    return False

def main_orchestrator():
    """ Orchestrates the entire shipping label creation process. """
    print("=============================================")
    print("===      PHASE 2: Shipping Workflow       ===")
    print("=============================================")
    retrieve_shipping_main()
    if not os.path.exists(PENDING_SHIPPING_FILE):
        print("INFO: No pending shipping file found. Nothing to process.")
        return
    with open(PENDING_SHIPPING_FILE, 'r') as f:
        try: orders_to_ship = json.load(f)
        except json.JSONDecodeError:
            print("ERROR: orders_pending_shipping.json is corrupted.")
            return
    if not orders_to_ship:
        print("INFO: No orders awaiting shipment.")
        return
    unprocessed_orders = [order for order in orders_to_ship if not has_label_been_created(order['order_id'])]
    if not unprocessed_orders:
        print("INFO: All shippable orders have already been processed.")
        return
    print(f"INFO: Found {len(unprocessed_orders)} new shippable orders to process.")
    with open(PENDING_SHIPPING_FILE, 'w') as f:
        json.dump(unprocessed_orders, f, indent=4)
    transform_data_main()
    create_labels_main()
    clear_shipped_orders_main()
    print("\n=============================================")
    print("===   Shipping Workflow Has Concluded     ===")
    print("=============================================")

if __name__ == '__main__':
    main_orchestrator()
