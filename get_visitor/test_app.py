import unittest
import os
from unittest.mock import patch

# Set TABLE_NAME so app.py doesn't break on import
os.environ["TABLE_NAME"] = "visitorCountTable"

import app  # Now safe to import

class TestLambdaHandler(unittest.TestCase):

    def test_lambda_handler_success(self):
        # Mock get_item method
        app.table.get_item = lambda Key: {'Item': {'count': 42}}

        result = app.lambda_handler({}, {})
        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(result['body'], '42')

    def test_lambda_handler_failure(self):
        # Simulate error
        def throw_error(Key):
            raise Exception("Simulated failure")

        app.table.get_item = throw_error

        result = app.lambda_handler({}, {})
        self.assertEqual(result['statusCode'], 500)
        self.assertIn("Error:", result['body'])

if __name__ == '__main__':
    unittest.main()
