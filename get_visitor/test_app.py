import unittest
from unittest.mock import patch
import app  # your Lambda code

class TestLambdaHandler(unittest.TestCase):

    @patch("app.boto3.resource")
    @patch("app.os.environ.get", return_value="visitorCountTable")
    def test_lambda_handler_success(self, mock_env, mock_boto3):
        mock_table = mock_boto3.return_value.Table.return_value
        mock_table.get_item.return_value = {
            "Item": {"count": 123}
        }

        event = {}
        context = {}
        response = app.lambda_handler(event, context)

        self.assertEqual(response["statusCode"], 200)
        self.assertIn("123", response["body"])

if __name__ == "__main__":
    unittest.main()
