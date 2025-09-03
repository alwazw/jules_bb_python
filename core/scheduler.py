import time
import sys
import os

# Add project root to the Python path to allow for absolute imports
# The script is in core/, so we need to go up one level to get to the project root.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from modules.acceptance import main_orchestrator as accept_orders_main
from modules.shipping import main_orchestrator as shipping_main
from modules.tracking import main_orchestrator as tracking_update_main
from modules.customer_service import main_orchestrator as customer_service_main

SCHEDULER_INTERVAL_SECONDS = 900 # 15 minutes

def main(run_once=False):
    """
    Master scheduler to run the entire order processing workflow.
    Can run in a loop or just once for testing.
    """
    print("=============================================")
    print("===      STARTING MASTER SCHEDULER        ===")
    print("=============================================")

    while True:
        print(f"\n\n\n{'='*20} RUNNING WORKFLOW CYCLE AT {time.ctime()} {'='*20}")

        # --- PHASE 1: ACCEPT NEW ORDERS ---
        print("\n>>> Checking for new orders to accept...")
        accept_orders_main()

        # --- PHASE 2: PROCESS SHIPPABLE ORDERS ---
        print("\n>>> Checking for shippable orders...")
        shipping_main()

        # --- PHASE 3: UPDATE TRACKING FOR SHIPPED ORDERS ---
        print("\n>>> Checking for shipped orders to update...")
        tracking_update_main()

        # --- PHASE 5: AGGREGATE CUSTOMER MESSAGES ---
        print("\n>>> Checking for new customer messages...")
        customer_service_main()

        print(f"\n{'='*20} WORKFLOW CYCLE COMPLETE {'='*20}")

        if run_once:
            print("--- Run-once flag detected. Scheduler will not loop. ---")
            break

        print(f"--- Scheduler sleeping for {SCHEDULER_INTERVAL_SECONDS / 60} minutes... ---")
        time.sleep(SCHEDULER_INTERVAL_SECONDS)


if __name__ == '__main__':
    # Basic argument parsing for standalone execution
    run_once_flag = '--run-once' in sys.argv
    main(run_once=run_once_flag)
