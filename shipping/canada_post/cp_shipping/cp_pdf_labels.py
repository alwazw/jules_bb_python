import os
import sys
import requests
import base64
import json
from datetime import datetime
import xml.etree.ElementTree as ET

# Add project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, '..', '..', '..'))
from common.utils import get_canada_post_credentials
from .validate_cp_shipment import get_shipment_details, get_tracking_summary
from .pdf_utils import watermark_pdf

# --- Configuration ---
LOGS_DIR_BB = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'logs', 'best_buy')
LOGS_DIR_CP = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'logs', 'canada_post')
XML_INPUT_DIR = os.path.join(LOGS_DIR_CP, 'create_label_xml_files')
PDF_OUTPUT_DIR = os.path.join(LOGS_DIR_CP, 'cp_pdf_shipping_labels')
VOIDED_PDF_DIR = os.path.join(PDF_OUTPUT_DIR, 'voided')
CP_SHIPPING_DATA_FILE = os.path.join(LOGS_DIR_CP, 'cp_shipping_labels_data.json')
CP_HISTORY_LOG_FILE = os.path.join(LOGS_DIR_CP, 'cp_shipping_history_log.json')
CUSTOMER_SERVICE_CP_HISTORY_LOG_FILE = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'logs', 'customer_service', 'cp_shipping_history_log.json')


def log_shipping_data(order_id, tracking_pin, label_url, void_url, api_response_text):
    """ Logs the shipping data to cp_shipping_labels_data.json. """
    os.makedirs(os.path.dirname(CP_SHIPPING_DATA_FILE), exist_ok=True)
    print(f"INFO: Logging shipping data for order {order_id}...")
    log_entries = []
    if os.path.exists(CP_SHIPPING_DATA_FILE):
        with open(CP_SHIPPING_DATA_FILE, 'r') as f:
            try:
                log_entries = json.load(f)
            except json.JSONDecodeError:
                print("WARNING: cp_shipping_labels_data.json is corrupted. Starting fresh.")

    log_entries.append({
        "order_id": order_id,
        "tracking_pin": tracking_pin,
        "label_url": label_url,
        "void_url": void_url,
        "timestamp": datetime.now().isoformat(),
        "api_response": api_response_text
    })

    with open(CP_SHIPPING_DATA_FILE, 'w') as f:
        json.dump(log_entries, f, indent=4)

def log_cp_history(shipment_details_xml):
    """ Appends the full shipment details XML to the history logs. """
    if not shipment_details_xml:
        return

    for log_path in [CP_HISTORY_LOG_FILE, CUSTOMER_SERVICE_CP_HISTORY_LOG_FILE]:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        log_entries = []
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                try:
                    log_entries = json.load(f)
                except json.JSONDecodeError:
                    log_entries = []

        log_entries.append({
            "timestamp": datetime.now().isoformat(),
            "shipment_details": shipment_details_xml
        })

        with open(log_path, 'w') as f:
            json.dump(log_entries, f, indent=4)
        print(f"SUCCESS: Appended shipment details to {log_path}")


def create_shipment_and_get_label(api_user, api_password, customer_number, xml_content, order):
    """ Sends the request to Canada Post, logs the data, and returns the label URL. """
    order_id = order['order_id']
    auth_string = f"{api_user}:{api_password}"
    auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    
    cp_api_url = f'https://soa-gw.canadapost.ca/rs/{customer_number}/{customer_number}/shipment'

    headers = {
        'Authorization': f'Basic {auth_b64}',
        'Content-Type': 'application/vnd.cpc.shipment-v8+xml',
        'Accept': 'application/vnd.cpc.shipment-v8+xml'
    }

    print("INFO: Sending request to Canada Post 'Create Shipment' API...")
    try:
        response = requests.post(cp_api_url, headers=headers, data=xml_content)
        response.raise_for_status()
        response_text = response.text
        print("SUCCESS: 'Create Shipment' API call was successful.")
        
        label_url, details_url, tracking_pin, void_url = None, None, None, None
        try:
            root = ET.fromstring(response_text)
            links = root.findall(".//{http://www.canadapost.ca/ws/shipment-v8}link")
            for link in links:
                if link.get('rel') == 'label':
                    label_url = link.get('href')
                elif link.get('rel') == 'details':
                    details_url = link.get('href')
                elif link.get('rel') == 'self':
                    void_url = link.get('href')


            tracking_pin_element = root.find(".//{http://www.canadapost.ca/ws/shipment-v8}tracking-pin")
            if tracking_pin_element is not None:
                tracking_pin = tracking_pin_element.text

        except ET.ParseError as e:
            print(f"ERROR: Failed to parse 'Create Shipment' response XML: {e}")

        log_shipping_data(order_id, tracking_pin, label_url, void_url, response_text)

        return label_url, details_url, tracking_pin

    except requests.exceptions.RequestException as e:
        print(f"ERROR: 'Create Shipment' API request failed: {e}")
        if e.response is not None:
            print("Response Body:", e.response.text)
            log_shipping_data(order_id, None, None, None, e.response.text)
        return None, None, None

def download_label(label_url, api_user, api_password, output_path):
    """ Downloads the shipping label PDF from the provided URL. """
    if not label_url:
        return

    auth_string = f"{api_user}:{api_password}"
    auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')

    headers = {
        'Accept': 'application/pdf',
        'Authorization': f'Basic {auth_b64}'
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

def main(order_id, order):
    """ Main function to process an XML file for a single order and get a PDF label. """
    print(f"\n--- Starting Create PDF Label for Order: {order_id} ---")

    os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)

    api_user, api_password, customer_number, _, _ = get_canada_post_credentials()
    if not all([api_user, api_password, customer_number]):
        return

    xml_file = f"{order_id}.xml"
    xml_path = os.path.join(XML_INPUT_DIR, xml_file)

    if not os.path.exists(xml_path):
        print(f"ERROR: XML file {xml_file} not found in {XML_INPUT_DIR}.")
        return

    print(f"\nINFO: Processing {xml_file} for order {order_id}...")
    
    with open(xml_path, 'r') as f:
        xml_content = f.read()

    label_url, details_url, tracking_pin = create_shipment_and_get_label(api_user, api_password, customer_number, xml_content, order)

    if details_url:
        shipment_details_xml = get_shipment_details(api_user, api_password, details_url)
        if shipment_details_xml:
            log_cp_history(shipment_details_xml)

    if tracking_pin:
        import time
        print("INFO: Waiting for 30 seconds for tracking pin to become active...")
        time.sleep(30)
        is_valid_tracking = get_tracking_summary(api_user, api_password, tracking_pin)
        if not is_valid_tracking:
            print(f"CRITICAL WARNING: Tracking PIN for order {order_id} could not be validated in real-time. Proceeding with Best Buy update.")

    if label_url:
        pdf_path = os.path.join(PDF_OUTPUT_DIR, f"{order_id}.pdf")
        download_label(label_url, api_user, api_password, pdf_path)

    print(f"--- Create PDF Label for Order: {order_id} Finished ---\n")

def void_shipment(order_id, api_user, api_password):
    """ Voids a shipment for a given order ID. """
    print(f"INFO: Attempting to void shipment for order {order_id}...")
    if not os.path.exists(CP_SHIPPING_DATA_FILE):
        print(f"WARNING: Shipping data file not found. Cannot void shipment for order {order_id}.")
        return False

    with open(CP_SHIPPING_DATA_FILE, 'r') as f:
        try:
            log_entries = json.load(f)
        except json.JSONDecodeError:
            print("ERROR: cp_shipping_labels_data.json is corrupted.")
            return False

    shipment_to_void = None
    for entry in reversed(log_entries):
        if entry.get("order_id") == order_id and entry.get("void_url"):
            shipment_to_void = entry
            break

    if not shipment_to_void:
        print(f"INFO: No previous shipment with a void_url found for order {order_id}. Nothing to void.")
        return True # Nothing to void is considered a success

    void_url = shipment_to_void['void_url']
    auth_string = f"{api_user}:{api_password}"
    auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')

    headers = {
        'Authorization': f'Basic {auth_b64}',
        'Accept': 'application/vnd.cpc.shipment-v8+xml'
    }

    try:
        response = requests.delete(void_url, headers=headers)
        if response.status_code == 204:
            print(f"SUCCESS: Shipment for order {order_id} has been voided.")

            # Watermark the old PDF
            pdf_path = os.path.join(PDF_OUTPUT_DIR, f"{order_id}.pdf")
            watermark_pdf(pdf_path, VOIDED_PDF_DIR)

            return True
        else:
            print(f"ERROR: Failed to void shipment for order {order_id}. Status: {response.status_code}, Body: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"ERROR: API request to void shipment failed for order {order_id}: {e}")
        return False

if __name__ == '__main__':
    # This script is not meant to be run directly anymore.
    # It should be called from main_shipping.py
    print("This script is designed to be imported and used by other parts of the application.")
