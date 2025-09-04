# Master Scheduler

The master scheduler is the heart of the application, responsible for running the entire order processing workflow in a continuous, automated fashion. The core logic for the scheduler is located in `core/scheduler.py`.

## How it Works

The scheduler runs an infinite loop that executes the entire workflow every 15 minutes (this interval is configurable in the script).

In each cycle, it performs the following actions in sequence by calling the main orchestrator function from each respective module:

1.  **Run `modules/acceptance.py`:** Checks for and accepts any new orders from the Best Buy marketplace.
2.  **Run `modules/shipping.py`:** Checks for any orders that are ready for shipment, creates Canada Post shipping labels, and validates the new shipments.
3.  **Run `modules/tracking.py`:** Updates Best Buy with the tracking numbers for the newly created shipments and marks them as shipped.
4.  **Run `modules/customer_service.py`:** Fetches new customer service messages from the marketplace API.

## How to Run

To start the scheduler, run the main application entry point from the root of the project:

```bash
python3 main.py
```

The scheduler will print detailed logs to the console as it progresses through each phase of the workflow. To stop the scheduler, press `Ctrl+C`.

For testing purposes, you can execute a single cycle of the workflow by using the `--run-once` flag:
```bash
python3 main.py --run-once
```
