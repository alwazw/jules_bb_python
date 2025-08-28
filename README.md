
# Best Buy Marketplace - Python Order Automation

This project provides a simple, command-line based Python application to automate the acceptance of orders and creation of shipping labels from the Best Buy Marketplace.

## Project Phases

This project is broken down into four distinct phases, each with its own main orchestrator script:

1.  **Phase 1: Order Acceptance (`main_acceptance.py`)** - Fetches and accepts new orders.
2.  **Phase 2: Retrieve for Shipping (`retrieve_pending_shipping.py`)** - Gets orders ready for shipment.
3.  **Phase 3: Create Shipping Labels (`main_shipping.py`)** - Generates XML payloads and creates Canada Post shipping labels.
4.  **Phase 4: Update Tracking Numbers (`main_tracking.py`)** - Updates Best Buy with the new tracking numbers.

## 🚀 Getting Started

### 1. Prerequisites

*   Python 3.6+

### 2. Installation

1.  **Clone the repository** and navigate into the directory.

2.  **Create and activate a virtual environment:**
    *   `python3 -m venv venv`
    *   On macOS/Linux: `source venv/bin/activate`
    *   On Windows: `.\venv\Scripts\activate`

3.  **Install dependencies:**
    *   `pip install requests`

4.  **Add your API Keys:**
    *   Open `secrets.txt` and ensure your Best Buy and Canada Post credentials are correct.
    *   **IMPORTANT:** In `shipping/canada_post/cp_shipping/cp_pdf_labels.py`, you must replace `"YOUR_CUSTOMER_NUMBER"` with your actual Canada Post customer number.

### 3. Running the Application

Run each phase in order using the main orchestrator scripts:

```bash
# Phase 1: Accept new orders
python3 main_acceptance.py

# Phase 2: Get orders ready for shipping
python3 Orders/awaiting_shipment/orders_awaiting_shipment/retrieve_pending_shipping.py

# Phase 3: Create shipping labels
python3 main_shipping.py

# Phase 4: Update tracking info on Best Buy
python3 main_tracking.py
