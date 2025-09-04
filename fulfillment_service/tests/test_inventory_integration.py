import unittest
import json
from unittest.mock import patch, MagicMock

# Add project root to path to allow importing 'app'
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from fulfillment_service.src.app import app
from fulfillment_service.src import app as main_app

class TestInventoryIntegration(unittest.TestCase):

    def setUp(self):
        """Set up a test client and clear sessions for each test."""
        self.app = app.test_client()
        self.app.testing = True
        main_app.fulfillment_sessions.clear()

    @patch('fulfillment_service.src.logic.inv_logic.get_stock_level')
    @patch('fulfillment_service.src.logic.find_order_by_id')
    def test_start_fulfillment_out_of_stock(self, mock_find_order, mock_get_stock):
        """Test that fulfillment cannot start for an out-of-stock item."""
        mock_find_order.return_value = {'order_id': 'ORDER-1', 'order_lines': [{'offer_sku': 'SKU-OUTOFSTOCK'}]}
        mock_get_stock.return_value = 0

        response = self.app.post('/api/fulfillment/start', data=json.dumps({'order_id': 'ORDER-1'}), content_type='application/json')

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn("out of stock", data['error'])

    @patch('fulfillment_service.src.app.inv.decrease_stock')
    @patch('fulfillment_service.src.logic.generate_shipping_label')
    def test_finalize_decrements_stock(self, mock_generate_label, mock_decrease_stock):
        """Test that finalizing an order correctly decrements the stock."""
        # Setup session
        order_id = "ORDER-2"
        sku = "SKU-INSTOCK"
        main_app.fulfillment_sessions[order_id] = {
            "order": {"order_id": order_id, "order_lines": [{"offer_sku": sku}]},
            "required_components": {"BAR-123": "RAM"},
            "scanned_components": {"RAM"}
        }

        mock_generate_label.return_value = ({"tracking_pin": "TRACK-123", "pdf_path": "/path/to/label.pdf"}, None)
        mock_decrease_stock.return_value = True

        response = self.app.post('/api/fulfillment/finalize', data=json.dumps({'order_id': order_id}), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        mock_decrease_stock.assert_called_once_with(sku)

    @patch('fulfillment_service.src.app.inv.load_inventory')
    def test_inventory_status_endpoint(self, mock_load_inventory):
        """Test the customer service inventory status endpoint."""
        # Test Case 1: In Stock
        mock_load_inventory.return_value = {"SKU-1": {"quantity": 10, "threshold": 2}}
        response = self.app.get('/api/inventory/status/SKU-1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data)['status'], "In Stock")

        # Test Case 2: Low Stock
        mock_load_inventory.return_value = {"SKU-2": {"quantity": 2, "threshold": 5}}
        response = self.app.get('/api/inventory/status/SKU-2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data)['status'], "Low Stock")

        # Test Case 3: Out of Stock
        mock_load_inventory.return_value = {"SKU-3": {"quantity": 0, "threshold": 2}}
        response = self.app.get('/api/inventory/status/SKU-3')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data)['status'], "Out of Stock")

        # Test Case 4: Not Found
        mock_load_inventory.return_value = {}
        response = self.app.get('/api/inventory/status/SKU-404')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
