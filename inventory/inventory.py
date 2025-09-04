import json
import os

# --- Path Configuration ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
INVENTORY_FILE = os.path.join(PROJECT_ROOT, 'inventory', 'inventory.json')

def load_inventory():
    """Loads the inventory data from the JSON file."""
    if not os.path.exists(INVENTORY_FILE):
        return {}
    try:
        with open(INVENTORY_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_inventory(inventory_data):
    """Saves the inventory data to the JSON file."""
    with open(INVENTORY_FILE, 'w') as f:
        json.dump(inventory_data, f, indent=2)

def get_stock_level(sku):
    """Gets the current stock level for a given SKU."""
    inventory = load_inventory()
    return inventory.get(sku, {}).get('quantity', 0)

def decrease_stock(sku, quantity=1):
    """Decreases the stock level for a given SKU."""
    inventory = load_inventory()
    if sku in inventory and inventory[sku]['quantity'] >= quantity:
        inventory[sku]['quantity'] -= quantity
        save_inventory(inventory)
        check_restock_alert(sku)
        return True
    return False

def add_stock(sku, quantity, threshold, cost):
    """Adds new stock for a given SKU."""
    inventory = load_inventory()
    if sku in inventory:
        inventory[sku]['quantity'] += quantity
    else:
        inventory[sku] = {'quantity': quantity, 'threshold': threshold, 'cost': cost}
    save_inventory(inventory)

def check_restock_alert(sku):
    """Checks if a SKU is below its restock threshold and prints an alert."""
    inventory = load_inventory()
    if sku in inventory:
        if inventory[sku]['quantity'] <= inventory[sku]['threshold']:
            print(f"ALERT: Stock for SKU {sku} is low ({inventory[sku]['quantity']}). Please restock.")
