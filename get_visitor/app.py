import boto3
import os
import json
from decimal import Decimal  # <-- ADD THIS

def lambda_handler(event, context):
    try:
        dynamodb = boto3.resource("dynamodb")
        table_name = os.environ.get("TABLE_NAME")
        table = dynamodb.Table(table_name)
        
        response = table.get_item(Key={'id': 'visitorCount'})
        count = int(response['Item']['count'])  # <-- CONVERT TO int
        
        return {
            "statusCode": 200,
            "headers": { "Access-Control-Allow-Origin": "*" },
            "body": json.dumps({ "count": count })  # <-- JSON OBJECT
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": { "Access-Control-Allow-Origin": "*" },
            "body": json.dumps({ "error": str(e) })
        }
# This code retrieves the visitor count from a DynamoDB table and returns it as a JSON response.