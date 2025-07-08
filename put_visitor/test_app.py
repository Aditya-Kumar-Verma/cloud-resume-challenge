import unittest
from unittest.mock import patch
import app  # assuming app.py is in the same directory

class TestPutVisitorFunction(unittest.TestCase):

    @patch("app.boto3.resource")
    @patch("app.os.environ.get", return_value="visitorCountTable")
    def test_lambda_handler_success(self, mock_env, mock_boto3):
        mock_table = mock_boto3.return_value.Table.return_value
        mock_table.update_item.return_value = {
            "Attributes": {"count": 42}
        }

        event = {}
        context = {}
        response = app.lambda_handler(event, context)

        self.assertEqual(response["statusCode"], 200)
        self.assertIn("Visitor count incremented to 42", response["body"])

    @patch("app.boto3.resource")
    @patch("app.os.environ.get", return_value="visitorCountTable")
    def test_lambda_handler_failure(self, mock_env, mock_boto3):
        mock_table = mock_boto3.return_value.Table.return_value
        mock_table.update_item.side_effect = Exception("Simulated DynamoDB failure")

        event = {}
        context = {}
        response = app.lambda_handler(event, context)

        self.assertEqual(response["statusCode"], 500)
        self.assertIn("Error: Simulated DynamoDB failure", response["body"])

if __name__ == "__main__":
    unittest.main()
# This code is a unit test for the Lambda function that increments a visitor count in a DynamoDB table.
# It uses the unittest framework and mocks the Boto3 DynamoDB resource to simulate interactions with