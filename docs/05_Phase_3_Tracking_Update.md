# Phase 3: Tracking and Status Update

This phase handles the final step of updating the order on the Best Buy Marketplace with the new tracking information.

## Module

-   `modules/tracking.py`

## Logic Flow

All logic for the tracking and status update phase has been consolidated into the `modules/tracking.py` file. The main orchestrator function, `main_orchestrator()`, executes the following steps:

1.  **Read Shipping Logs:** The script reads the local logs created by the shipping module to get the list of recently created shipments and their corresponding tracking numbers.

2.  **Update Tracking on Best Buy:** For each new shipment, the script makes a `PUT` request to the Best Buy API's `/tracking` endpoint to add the Canada Post carrier code and the new tracking number to the order.

3.  **Mark Order as Shipped:** Immediately after adding the tracking number, a second `PUT` request is sent to the `/ship` endpoint. This is the action that updates the order's status to `SHIPPED` and notifies the customer.

4.  **Log Final Order State:** After a successful update, the script makes a final `GET` request to download the full details of the now-shipped order and saves it to a history log file for auditing.

5.  **Validate Final Status:** The script makes one last check to confirm that the order's status on the marketplace is indeed `SHIPPED`.
