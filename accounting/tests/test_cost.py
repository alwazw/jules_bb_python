import unittest
import json
import os
from unittest.mock import patch, mock_open

# Add project root to path to allow importing 'accounting'
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

from accounting import cost

class TestCost(unittest.TestCase):

    def setUp(self):
        """Set up test data."""
        self.mock_inventory_data = {
            "SKU-A": {"quantity": 10, "cost": 100, "threshold": 2},
            "SKU-B": {"quantity": 5, "cost": 200, "threshold": 1}
        }
        self.mock_products_data = [
            {"base_product": {"series": "Category A"}, "variants": [{"sku": "SKU-A"}]},
            {"base_product": {"series": "Category B"}, "variants": [{"sku": "SKU-B"}]}
        ]
        self.mock_orders_data = [
            {"order_id": "ORDER-1", "total_price": 150, "order_lines": [{"offer_sku": "SKU-A"}]}
        ]
        self.mock_cogs_data = '[{"order_id": "ORDER-1", "sku": "SKU-A", "cogs": 100}]'

    @patch('accounting.cost.inv.load_inventory')
    def test_calculate_inventory_value(self, mock_load_inventory):
        mock_load_inventory.return_value = self.mock_inventory_data
        value = cost.calculate_inventory_value()
        self.assertEqual(value, 10 * 100 + 5 * 200)

    @patch('builtins.open', new_callable=mock_open, read_data='[{"base_product": {"series": "Category A"}, "variants": [{"sku": "SKU-A"}]}, {"base_product": {"series": "Category B"}, "variants": [{"sku": "SKU-B"}]}]')
    @patch('accounting.cost.inv.load_inventory')
    def test_get_inventory_value_by_category(self, mock_load_inventory, mock_file):
        mock_load_inventory.return_value = self.mock_inventory_data
        category_values = cost.get_inventory_value_by_category()
        self.assertEqual(category_values, {"Category A": 1000, "Category B": 1000})

    @patch('builtins.open', new_callable=mock_open)
    @patch('accounting.cost.inv.load_inventory')
    def test_record_cogs(self, mock_load_inventory, mock_file):
        mock_load_inventory.return_value = self.mock_inventory_data
        cost.record_cogs("ORDER-1", "SKU-A", 1)
        mock_file().write.assert_called()

    @patch('builtins.open', new_callable=mock_open, read_data='[{"order_id": "ORDER-1", "total_price": 150}]')
    @patch('accounting.cost.os.path.exists', return_value=True)
    def test_get_order_details(self, mock_exists, mock_file):
        order = cost.get_order_details("ORDER-1")
        self.assertEqual(order['total_price'], 150)

    @patch('accounting.cost.get_order_details')
    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open)
    def test_calculate_profitability(self, mock_open, mock_exists, mock_get_order_details):
        mock_get_order_details.return_value = {"order_id": "ORDER-1", "total_price": 150}
        mock_open.return_value.read.return_value = self.mock_cogs_data

        # Re-mock open for the json.load call
        m = mock_open
        m.return_value.__enter__.return_value.read.return_value = self.mock_cogs_data

        profitability = cost.calculate_profitability("ORDER-1")

        self.assertEqual(profitability['profit'], 50)
        self.assertAlmostEqual(profitability['margin_percent'], 33.33, places=2)


if __name__ == '__main__':
    unittest.main()
