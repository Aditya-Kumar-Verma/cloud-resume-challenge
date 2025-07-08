import json
import boto3
import os

# Initialize DynamoDB resource and table
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    """
    Lambda function to increment and return the visitor count stored in DynamoDB.

    Returns
    -------
    dict
        JSON response containing updated visitor count and CORS headers.
    """

    try:
        # Update or create 'visitor' item and increment its counter
        response = table.update_item(
            Key={'id': 'visitor'},
            UpdateExpression='ADD visit_count :incr',
            ExpressionAttributeValues={':incr': 1},
            ReturnValues='UPDATED_NEW'
        )

        new_count = int(response['Attributes']['visit_count'])

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",  # Enable CORS
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*"
            },
            "body": json.dumps({"count": new_count})
        }

    except Exception as e:
        print("Error:", e)
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*"
            },
            "body": json.dumps({"error": "Internal Server Error"})
        }
