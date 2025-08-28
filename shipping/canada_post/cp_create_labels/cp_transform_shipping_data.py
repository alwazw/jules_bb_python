
import os 
import json 
import xml.etree.ElementTree as ET from xml.dom 
import minidom

--- Configuration ---
ORDERS_FILE = os.path.join(os.path.dirname(file), '..', '..', '..', 'Orders', 'awaiting_shipment', 'orders_awaiting_shipment', 'orders_pending_shipping.json') XML_OUTPUT_DIR = os.path.join(os.path.dirname(file), 'create_label_xml_files') SENDER_COMPANY = "VISIONVATION INC." SENDER_CONTACT_PHONE = "647-444-0848" SENDER_ADDRESS = "133 Rock Feen Way" SENDER_CITY = "North York" SENDER_PROVINCE = "ON" SENDER_POSTAL_CODE = "M2J 4N3" CP_CONTRACT_ID = "0043924574"

def create_xml_payload(order): """ Creates the XML payload for a single order. """ order_id = order['order_id'] customer = order['customer'] shipping = customer['shipping_address'] offer_sku = order['order_lines'][0]['offer_sku'] quantity = order['order_lines'][0]['quantity']

shipment = ET.Element('shipment', xmlns="http://www.canadapost.ca/ws/shipment-v8")
group_id = ET.SubElement(shipment, 'group-id')
group_id.text = order_id
delivery_spec = ET.SubElement(shipment, 'delivery-spec')
service_code = ET.SubElement(delivery_spec, 'service-code')
service_code.text = 'DOM.EP'
sender = ET.SubElement(delivery_spec, 'sender')
sender_company = ET.SubElement(sender, 'company')
sender_company.text = SENDER_COMPANY
sender_phone = ET.SubElement(sender, 'contact-phone')
sender_phone.text = SENDER_CONTACT_PHONE
sender_address_details = ET.SubElement(sender, 'address-details')
ET.SubElement(sender_address_details, 'address-line-1').text = SENDER_ADDRESS
ET.SubElement(sender_address_details, 'city').text = SENDER_CITY
ET.SubElement(sender_address_details, 'prov-state').text = SENDER_PROVINCE
ET.SubElement(sender_address_details, 'postal-code').text = SENDER_POSTAL_CODE
destination = ET.SubElement(delivery_spec, 'destination')
dest_name = ET.SubElement(destination, 'name')
dest_name.text = f"{shipping['firstname']} {shipping['lastname']}"
dest_company = ET.SubElement(destination, 'company')
dest_company.text = f"{quantity}x {offer_sku}"
dest_address_details = ET.SubElement(destination, 'address-details')
ET.SubElement(dest_address_details, 'address-line-1').text = shipping['street_1']
ET.SubElement(dest_address_details, 'city').text = shipping['city']
ET.SubElement(dest_address_details, 'prov-state').text = shipping['state']
ET.SubElement(dest_address_details, 'country-code').text = 'CA'
ET.SubElement(dest_address_details, 'postal-code').text = shipping['zip_code']
dest_phone = ET.SubElement(destination, 'contact-phone')
dest_phone.text = shipping.get('phone', '')
options = ET.SubElement(delivery_spec, 'options')
option_sig = ET.SubElement(options, 'option')
ET.SubElement(option_sig, 'option-code').text = 'SO'
option_dns = ET.SubElement(options, 'option')
ET.SubElement(option_dns, 'option-code').text = 'DNS'
parcel_characteristics = ET.SubElement(delivery_spec, 'parcel-characteristics')
ET.SubElement(parcel_characteristics, 'weight').text = '1.8'
dimensions = ET.SubElement(parcel_characteristics, 'dimensions')
ET.SubElement(dimensions, 'length').text = '35'
ET.SubElement(dimensions, 'width').text = '25'
ET.SubElement(dimensions, 'height').text = '5'
notification = ET.SubElement(delivery_spec, 'notification')
ET.SubElement(notification, 'email').text = order.get('customer_notification_email', '')
ET.SubElement(notification, 'on-shipment').text = 'true'
ET.SubElement(notification, 'on-delivery').text = 'true'
settlement_info = ET.SubElement(delivery_spec, 'settlement-info')
ET.SubElement(settlement_info, 'contract-id').text = CP_CONTRACT_ID
ET.SubElement(settlement_info, 'intended-method-of-payment').text = 'Account'

xml_str = ET.tostring(shipment, 'utf-8')
dom = minidom.parseString(xml_str)
return dom.toprettyxml(indent="  ")
def main(): """ Main function to read orders and generate XML files. """ print("\n--- Starting Transform Shipping Data to XML Script ---")

os.makedirs(XML_OUTPUT_DIR, exist_ok=True)

if not os.path.exists(ORDERS_FILE):
    print(f"ERROR: orders_pending_shipping.json not found at {ORDERS_FILE}")
    return

with open(ORDERS_FILE, 'r') as f:
    try:
        orders = json.load(f)
    except json.JSONDecodeError:
        print("ERROR: orders_pending_shipping.json is corrupted.")
        return
        
if not orders:
    print("INFO: No orders found in orders_pending_shipping.json to process.")
    return

print(f"INFO: Found {len(orders)} orders to process.")

for order in orders:
    order_id = order['order_id']
    print(f"INFO: Processing order {order_id}...")
    
    xml_content = create_xml_payload(order)
    
    xml_filename = os.path.join(XML_OUTPUT_DIR, f"{order_id}.xml")
    with open(xml_filename, 'w') as xml_file:
        xml_file.write(xml_content)
        
    print(f"SUCCESS: Created XML file: {xml_filename}")
    
print("--- Transform Shipping Data to XML Script Finished ---\n")
if name == 'main': main() 
