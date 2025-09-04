# Best Buy Marketplace - Python Order Automation

This project provides a command-line based Python application to automate the order fulfillment workflow for the Best Buy Marketplace, including order acceptance, shipping label creation, and customer service message aggregation.

## Project Status
This project has undergone a major refactoring to establish a modular and scalable architecture (V2). The new structure is in place, and development is focused on building out a new database-driven fulfillment process with a web-based GUI.

## Project Architecture

The project is now organized into a modular structure:

-   `main.py`: The single entry point for the application. It starts the core scheduler.
-   `core/`: This directory contains the central application logic.
    -   `scheduler.py`: The master scheduler that orchestrates the execution of all modules in a timed loop.
    -   `utils.py`: Shared utility functions, such as loading API credentials.
-   `modules/`: This directory contains the business logic for each phase of the workflow.
    -   `acceptance.py`: Handles fetching and accepting new orders.
    -   `shipping.py`: Handles creating shipping labels.
    -   `tracking.py`: Handles updating tracking information on the marketplace.
    -   `customer_service.py`: Handles fetching customer service messages.
-   `database/`: Contains the database schema (`schema.sql`) for the V2 implementation.
-   `web_ui/`: Contains the Flask web application for the V2 Fulfillment Dashboard.

## 🚀 Getting Started

### 1. Prerequisites

*   Python 3.6+
*   The `requests`, `SQLAlchemy`, `psycopg2-binary`, and `Flask` libraries.

### 2. Installation

1.  **Clone the repository** and navigate into the directory.

2.  **Create and activate a virtual environment:**
    *   `python3 -m venv venv`
    *   On macOS/Linux: `source venv/bin/activate`
    *   On Windows: `.\venv\Scripts\activate`

3.  **Install dependencies:**
    *   `pip install -r requirements.txt` (Note: A `requirements.txt` file should be created).

4.  **Add your API Keys:**
    *   Open `secrets.txt` and add your Best Buy and Canada Post credentials.

### 3. Running the Application

To run the entire automated workflow, use the main entry point:

```bash
# This will start the master scheduler, which runs the full workflow every 15 minutes.
python3 main.py
```

For testing, you can run a single cycle of the scheduler:
```bash
python3 main.py --run-once
```

## V2 Development

The next phase of development (V2) is focused on replacing the current file-based logging and state management with a robust PostgreSQL database and a web-based GUI for operators. The foundational files for this are already in place. See `docs/V2_Simulation_and_Findings.md` for more details on the target architecture.
