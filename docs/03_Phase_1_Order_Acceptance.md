# Phase 1: Order Acceptance

This phase handles the detection and acceptance of new orders from the Best Buy Marketplace.

## Module

-   `modules/acceptance.py`

## Logic Flow

All logic for the order acceptance phase has been consolidated into the `modules/acceptance.py` file. The main orchestrator function, `main_orchestrator()`, executes the following steps in a loop until all pending orders are successfully accepted:

1.  **Retrieve Pending Orders:** It calls the Best Buy API to get all orders currently in the `WAITING_ACCEPTANCE` state. These orders are saved to a local log file.

2.  **Accept Orders:** The script iterates through the pending orders and makes individual API calls to accept each one. The results of these acceptance calls are logged.

3.  **Validate Acceptance:** After attempting to accept the orders, the script makes another API call to get a fresh list of pending orders. It compares this list to its internal log of accepted orders to validate that the process was successful. If any new orders have arrived during this process, the loop repeats.
