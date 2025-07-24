import unittest
from unittest.mock import patch
import app
import json

class TestPutVisitorFunction(unittest.TestCase):

    @patch("app.boto3.resource")
    @patch("app.os.environ.get", return_value="visitorCountTable")
    def test_lambda_handler_success(self, mock_env, mock_boto3):
        mock_table = mock_boto3.return_value.Table.return_value
        mock_table.update_item.return_value = {"Attributes": {"count": 42}}

        event = {}
        context = {}
        response = app.lambda_handler(event, context)

        print("RESPONSE:", response)

        self.assertEqual(response["statusCode"], 200)

        body = json.loads(response["body"])
        self.assertEqual(body["count"], 42)

    @patch("app.boto3.resource")
    @patch("app.os.environ.get", return_value="visitorCountTable")
    def test_lambda_handler_failure(self, mock_env, mock_boto3):
        mock_table = mock_boto3.return_value.Table.return_value
        mock_table.update_item.side_effect = Exception("Simulated DynamoDB failure")

        event = {}
        context = {}
        response = app.lambda_handler(event, context)

        self.assertEqual(response["statusCode"], 500)

        body = json.loads(response["body"])
        self.assertEqual(body["error"], "Simulated DynamoDB failure")

if __name__ == "__main__":
    unittest.main()
