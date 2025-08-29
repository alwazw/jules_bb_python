import os
import sys
import json

# Add project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from Orders.awaiting_shipment.orders_awaiting_shipment.retrieve_pending_shipping import main as retrieve_shipping_main
from shipping.canada_post.cp_create_labels.cp_transform_shipping_data import main as transform_data_main
from shipping.canada_post.cp_shipping.cp_pdf_labels import main as create_labels_main, void_shipment
from common.utils import get_canada_post_credentials

LOGS_DIR_CP = os.path.join(os.path.dirname(__file__), 'logs', 'canada_post')
CP_HISTORY_LOG_FILE = os.path.join(LOGS_DIR_CP, 'cp_shipping_history_log.json')
LOGS_DIR_BB = os.path.join(os.path.dirname(__file__), 'logs', 'best_buy')
PENDING_SHIPPING_FILE = os.path.join(LOGS_DIR_BB, 'orders_pending_shipping.json')


def process_shippable_orders():
    """
    Orchestrates the entire shipping label creation process.
    If a label already exists for an order, it is voided before a new one is created.
    """
    print("=============================================")
    print("===      Running Shipping Workflow        ===")
    print("=============================================")

    # Get CP credentials once
    api_user, api_password, _, _, _ = get_canada_post_credentials()
    if not all([api_user, api_password]):
        print("ERROR: Could not retrieve Canada Post credentials. Aborting.")
        return

    # First, get the latest list of shippable orders from Best Buy
    retrieve_shipping_main()

    # Now, process the orders found in the pending shipping file
    if not os.path.exists(PENDING_SHIPPING_FILE):
        print("INFO: No pending shipping file found. Nothing to process.")
        return

    with open(PENDING_SHIPPING_FILE, 'r') as f:
        try:
            orders_to_ship = json.load(f)
        except json.JSONDecodeError:
            print("ERROR: orders_pending_shipping.json is corrupted.")
            return

    if not orders_to_ship:
        print("INFO: No orders awaiting shipment.")
        return

    print(f"INFO: Found {len(orders_to_ship)} shippable orders to process.")

    for order in orders_to_ship:
        order_id = order['order_id']
        print(f"\n--- Processing Order: {order_id} ---")

        # 1. Void any existing shipment for this order
        # This will also watermark and move the old PDF if it exists
        void_shipment(order_id, api_user, api_password)

        # 2. Transform data and create XML for the new shipment
        transform_data_main(order)

        # 3. Create the new shipping label
        create_labels_main(order_id, order)

    print("\n=============================================")
    print("===   Shipping Workflow Has Concluded     ===")
    print("=============================================")

if __name__ == '__main__':
    process_shippable_orders()
