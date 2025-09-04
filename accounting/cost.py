import json
import os
from datetime import datetime

# --- Path Configuration ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
INVENTORY_FILE = os.path.join(PROJECT_ROOT, 'inventory', 'inventory.json')
COGS_LOG_FILE = os.path.join(PROJECT_ROOT, 'accounting', 'cogs_log.json')

# Add project root to path to allow importing 'inventory'
import sys
sys.path.insert(0, PROJECT_ROOT)
from inventory import inventory as inv

def calculate_inventory_value():
    """Calculates the total value of the current inventory."""
    inventory = inv.load_inventory()
    total_value = 0
    for sku, data in inventory.items():
        total_value += data.get('quantity', 0) * data.get('cost', 0)
    return total_value

def record_cogs(sku, quantity):
    """Records the Cost of Goods Sold (COGS) for a fulfilled item."""
    inventory = inv.load_inventory()
    cost = inventory.get(sku, {}).get('cost', 0)
    cogs_entry = {
        'timestamp': datetime.now().isoformat(),
        'sku': sku,
        'quantity': quantity,
        'cogs': cost * quantity
    }

    log_data = []
    if os.path.exists(COGS_LOG_FILE):
        with open(COGS_LOG_FILE, 'r') as f:
            try:
                log_data = json.load(f)
            except json.JSONDecodeError:
                pass # Overwrite if file is corrupt

    log_data.append(cogs_entry)

    with open(COGS_LOG_FILE, 'w') as f:
        json.dump(log_data, f, indent=2)

if __name__ == '__main__':
    # Example usage:
    print(f"Total Inventory Value: ${calculate_inventory_value():.2f}")
    # To test COGS recording:
    # record_cogs('FB-LPP1-G1-16-512', 1)
    # print("Recorded COGS for 1 unit of FB-LPP1-G1-16-512.")
    # print(f"New Total Inventory Value: ${calculate_inventory_value():.2f}")
