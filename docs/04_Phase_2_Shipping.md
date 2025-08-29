# Phase 2: Shipping Label Creation

This phase handles the creation of Canada Post shipping labels for orders that are ready for shipment. It has been refactored for robustness to prevent duplicate labels and provide a clear audit trail.

## Orchestrator: `main_shipping.py`

This is the master script for this phase. It orchestrates the entire workflow in a sequential, per-order basis.

### Workflow Steps:
1.  **Get Shippable Orders:** It first calls `retrieve_pending_shipping.py` to get the latest list of orders in the `SHIPPING` state from Best Buy.
2.  **Process Orders Individually:** It then iterates through each shippable order and performs the following steps:
    a. **Void Existing Shipment:** It calls the `void_shipment` function from `cp_pdf_labels.py`. If a shipment for the order already exists in the logs, this function sends a `DELETE` request to the Canada Post API to void it.
    b. **Watermark and Archive PDF:** If a shipment was successfully voided, the `watermark_pdf` utility is called to stamp the old PDF label with "VOIDED" and move it to the `logs/canada_post/cp_pdf_shipping_labels/voided/` directory.
    c. **Transform Data:** It calls `transform_data_main`, passing in the order details to generate a new XML payload for Canada Post.
    d. **Create New Label:** It calls `create_labels_main`, passing in the order details to create a new, valid shipment and download the PDF label.

## Core Scripts

1.  **`Orders/awaiting_shipment/orders_awaiting_shipment/retrieve_pending_shipping.py`**
    -   **Purpose:** Retrieves all orders with the status `SHIPPING` from the Best Buy API.
    -   **Output:** Saves the retrieved orders to `logs/best_buy/orders_pending_shipping.json`.

2.  **`shipping/canada_post/cp_create_labels/cp_transform_shipping_data.py`**
    -   **Purpose:** Contains the `main` function that accepts a single order's data and transforms it into the required XML format for the Canada Post API.
    -   **Output:** Creates one `.xml` file for the order in `logs/canada_post/create_label_xml_files/`.

3.  **`shipping/canada_post/cp_shipping/cp_pdf_labels.py`**
    -   **Purpose:** This script now contains the core logic for interacting with the Canada Post shipment API.
    -   `main()`: Processes a single order to create a shipment and download the PDF label. It saves the PDF to `logs/canada_post/cp_pdf_shipping_labels/` with a clean `{order_id}.pdf` filename.
    -   `void_shipment()`: Contains the logic to send the `DELETE` request to the Canada Post API to void a shipment.
    -   **Output:**
        -   Saves the new PDF label to `logs/canada_post/cp_pdf_shipping_labels/`.
        -   Logs the raw API responses and the crucial `void_url` to `logs/canada_post/cp_shipping_labels_data.json`.

4.  **`shipping/canada_post/cp_shipping/pdf_utils.py` (New)**
    -   **Purpose:** A new utility module that handles PDF manipulation.
    -   `watermark_pdf()`: Uses the `PyMuPDF` library to add a "VOIDED" watermark to a PDF file.

5.  **`shipping/canada_post/cp_shipping/validate_cp_shipment.py`**
    -   **Purpose:** Contains functions to validate the newly created shipment.
    -   `get_shipment_details`: Fetches the full shipment details from Canada Post and logs them to history files.
    -   `get_tracking_summary`: Makes a call to the public tracking API to confirm the tracking PIN is active.
