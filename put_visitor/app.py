import boto3
import os

def lambda_handler(event, context):
    try:
        table_name = os.environ.get("TABLE_NAME")
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(table_name)

        response = table.update_item(
            Key={"id": "visitorCount"},
            UpdateExpression="ADD #c :inc",
            ExpressionAttributeNames={"#c": "count"},
            ExpressionAttributeValues={":inc": 1},
            ReturnValues="UPDATED_NEW"
        )

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "PUT,OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": f"Visitor count incremented to {int(response['Attributes']['count'])}"
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "PUT,OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": f"Error: {str(e)}"
        }
# Note: Ensure that the environment variable TABLE_NAME is set to your DynamoDB table name.
# This code increments the visitor count in the DynamoDB table and returns the updated count.