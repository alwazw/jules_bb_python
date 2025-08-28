
import os import requests 
import base64 
import json from datetime 
import datetime

--- Configuration ---
XML_INPUT_DIR = os.path.join(os.path.dirname(file), '..', 'cp_create_labels', 'create_label_xml_files') PDF_OUTPUT_DIR = os.path.join(os.path.dirname(file), 'cp_pdf_shipping_labels') SECRETS_FILE = os.path.join(os.path.dirname(file), '..', '..', '..', 'secrets.txt') CP_SHIPPING_DATA_FILE = os.path.join(os.path.dirname(file), 'cp_shipping_labels_data.json') CUSTOMER_SERVICE_LOG_FILE = os.path.join(os.path.dirname(file), '..', '..', 'customer_service_logs', 'customer_service_shipping_log.json') YOUR_CUSTOMER_NUMBER = "YOUR_CUSTOMER_NUMBER" CP_API_URL = f'https://soa-gw.canadapost.ca/rs/{YOUR_CUSTOMER_NUMBER}/{YOUR_CUSTOMER_NUMBER}/shipment'

def get_cp_credentials(): """ Reads the Canada Post API credentials from the secrets.txt file. """ print("INFO: Reading Canada Post credentials from secrets.txt...") user, password = None, None try: with open(SECRETS_FILE, 'r') as f: for line in f: if line.startswith('CANADA_POST_API_USER='): user = line.strip().split('=')[1] elif line.startswith('CANADA_POST_API_PASSWORD='): password = line.strip().split('=')[1] if user and password: print("SUCCESS: Canada Post credentials loaded.") return user, password except FileNotFoundError: print(f"ERROR: secrets.txt not found at {SECRETS_FILE}") return None, None

def log_shipping_data(order_id, tracking_pin, label_url, api_response_text): """ Logs the shipping data to cp_shipping_labels_data.json. """ print(f"INFO: Logging shipping data for order {order_id}...") log_entries = [] if os.path.exists(CP_SHIPPING_DATA_FILE): with open(CP_SHIPPING_DATA_FILE, 'r') as f: try: log_entries = json.load(f) except json.JSONDecodeError: print("WARNING: cp_shipping_labels_data.json is corrupted. Starting fresh.")

log_entries.append({
    "order_id": order_id,
    "tracking_pin": tracking_pin,
    "label_url": label_url,
    "timestamp": datetime.now().isoformat(),
    "api_response": api_response_text
})

with open(CP_SHIPPING_DATA_FILE, 'w') as f:
    json.dump(log_entries, f, indent=4)
def log_for_customer_service(order_id, customer_name, shipping_address, tracking_pin): """ Logs key shipping details for easy customer service lookup. """ print(f"INFO: Logging to customer service log for order {order_id}...") log_entries = [] if os.path.exists(CUSTOMER_SERVICE_LOG_FILE): with open(CUSTOMER_SERVICE_LOG_FILE, 'r') as f: try: log_entries = json.load(f) except json.JSONDecodeError: pass

log_entries.append({
    "order_reference": order_id,
    "customer_name": customer_name,
    "shipping_address": shipping_address,
    "tracking_number": tracking_pin,
    "log_timestamp": datetime.now().isoformat()
})

with open(CUSTOMER_SERVICE_LOG_FILE, 'w') as f:
    json.dump(log_entries, f, indent=4)
def create_shipment_and_get_label(api_user, api_password, xml_content, order): """ Sends the request to Canada Post, logs the data, and returns the label URL. """ order_id = order['order_id'] auth_string = f"{api_user}:{api_password}" auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')

headers = {
    'Authorization': f'Basic {auth_b64}',
    'Content-Type': 'application/vnd.cpc.shipment-v8+xml',
    'Accept': 'application/vnd.cpc.shipment-v8+xml'
}

print("INFO: Sending request to Canada Post 'Create Shipment' API...")
try:
    response = requests.post(CP_API_URL, headers=headers, data=xml_content)
    response.raise_for_status()
    response_text = response.text
    print("SUCCESS: 'Create Shipment' API call was successful.")
    
    tracking_pin, label_url = None, None
    if '<tracking-pin>' in response_text:
        start = response_text.find('<tracking-pin>') + 14
        end = response_text.find('</tracking-pin>', start)
        tracking_pin = response_text[start:end]
    
    if '<link rel="label"' in response_text:
        start = response_text.find('href="') + 6
        end = response_text.find('"', start)
        label_url = response_text[start:end]
        
    log_shipping_data(order_id, tracking_pin, label_url, response_text)
    
    if tracking_pin:
        customer = order['customer']
        shipping = customer['shipping_address']
        customer_name = f"{shipping['firstname']} {shipping['lastname']}"
        full_address = f"{shipping['street_1']}, {shipping['city']}, {shipping['state']} {shipping['zip_code']}"
        log_for_customer_service(order_id, customer_name, full_address, tracking_pin)

    return label_url

except requests.exceptions.RequestException as e:
    print(f"ERROR: 'Create Shipment' API request failed: {e}")
    if e.response is not None:
        log_shipping_data(order_id, None, None, e.response.text)
    return None
def download_label(label_url, output_path): """ Downloads the shipping label PDF from the provided URL. """ if not label_url: return

headers = {
    'Accept': 'application/pdf'
}

print(f"INFO: Downloading label from {label_url}...")
try:
    response = requests.get(label_url, headers=headers)
    response.raise_for_status()
    
    with open(output_path, 'wb') as f:
        f.write(response.content)
        
    print(f"SUCCESS: Saved label to {output_path}")

except requests.exceptions.RequestException as e:
    print(f"ERROR: Failed to download label: {e}")
def main(): """ Main function to process XML files and get PDF labels. """ print("\n--- Starting Create PDF Labels Script ---")

os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(CUSTOMER_SERVICE_LOG_FILE), exist_ok=True)

api_user, api_password = get_cp_credentials()
if not api_user or not api_password:
    return
    
xml_files = [f for f in os.listdir(XML_INPUT_DIR) if f.endswith('.xml')]

if not xml_files:
    print("INFO: No XML files found to process.")
    return
    
print(f"INFO: Found {len(xml_files)} XML files to process.")

# Load all pending orders to have access to full order details
with open(os.path.join(os.path.dirname(XML_INPUT_DIR), '..', '..', '..', 'Orders', 'awaiting_shipment', 'orders_awaiting_shipment', 'orders_pending_shipping.json'), 'r') as f:
    all_orders = json.load(f)
orders_map = {order['order_id']: order for order in all_orders}

for xml_file in xml_files:
    order_id = os.path.splitext(xml_file)[0]
    xml_path = os.path.join(XML_INPUT_DIR, xml_file)
    
    print(f"\nINFO: Processing {xml_file} for order {order_id}...")
    
    with open(xml_path, 'r') as f:
        xml_content = f.read()
    
    order_details = orders_map.get(order_id)
    if not order_details:
        print(f"WARNING: Could not find order details for {order_id}. Skipping.")
        continue

    label_url = create_shipment_and_get_label(api_user, api_password, xml_content, order_details)
    
    if label_url:
        pdf_path = os.path.join(PDF_OUTPUT_DIR, f"{order_id}.pdf")
        download_label(label_url, pdf_path)
        
print("--- Create PDF Labels Script Finished ---\n")
if name == 'main': main() 
