# Best Buy Marketplace - Python Order Automation

This project provides a command-line based Python application to automate the order fulfillment workflow for the Best Buy Marketplace, from order acceptance to shipping.

## Project Status
The core order management and shipping workflow is complete and stable. The project is now moving into the development of a new Customer Service module.

## Core Workflow

The application is designed to be run as a series of scripts, orchestrated by `main_scheduler.py` for full automation. The workflow consists of three main parts:

1.  **Order Acceptance (`main_acceptance.py`)**: Fetches and accepts new orders from the Best Buy API.
2.  **Shipping Label Creation (`main_shipping.py`)**:
    *   Retrieves orders that are ready for shipment.
    *   For each order, it voids any previously created labels to prevent duplicates.
    *   It then creates a new, valid Canada Post shipping label and saves it as a PDF.
3.  **Tracking Update (`main_tracking.py`)**: Updates the order on Best Buy with the new tracking number and marks it as shipped.

## 🚀 Getting Started

### 1. Prerequisites

*   Python 3.6+
*   A virtual environment is recommended.

### 2. Installation

1.  **Clone the repository** and navigate into the directory.

2.  **Create and activate a virtual environment:**
    *   `python3 -m venv venv`
    *   On macOS/Linux: `source venv/bin/activate`
    *   On Windows: `.\venv\Scripts\activate`

3.  **Install dependencies:**
    *   `pip install -r requirements.txt`

4.  **Add your API Keys:**
    *   Create a file named `secrets.txt` in the root directory and add your Best Buy and Canada Post credentials in the format specified in `common/utils.py`.

### 3. Running the Application

You can run each phase of the workflow manually using the main orchestrator scripts:

```bash
# 1. Accept new orders
python3 main_acceptance.py

# 2. Create shipping labels
python3 main_shipping.py

# 3. Update tracking info on Best Buy
python3 main_tracking.py
```

For continuous, automated operation, you can run the master scheduler:
```bash
python3 main_scheduler.py
```
