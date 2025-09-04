# Phase 2: Shipping Label Creation

This phase handles the creation of Canada Post shipping labels for orders that are ready for shipment.

## Module

-   `modules/shipping.py`

## Logic Flow

All logic for the shipping label creation phase has been consolidated into the `modules/shipping.py` file. The main orchestrator function, `main_orchestrator()`, executes the following steps:

1.  **Retrieve Shippable Orders:** The script first calls the Best Buy API to get a fresh list of all orders in the `SHIPPING` state.

2.  **Check for Duplicates:** It compares the list of shippable orders against its own history logs to identify orders that have not yet been processed.

3.  **Transform Data to XML:** For each new shippable order, the script transforms the order data into the complex XML format required by the Canada Post "Create Shipment" API.

4.  **Create Canada Post Shipment:** The script sends the XML payload to the Canada Post API. This is a live, billable transaction that creates a real shipment.

5.  **Download PDF Label:** From the API response, the script extracts a link to the 4x6 shipping label and downloads the PDF to a local log directory.

6.  **Validate Shipment:** The script makes secondary calls to the Canada Post API to fetch the full shipment details and to validate that the new tracking PIN is active and recognized by the system.
