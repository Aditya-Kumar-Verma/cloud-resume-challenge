import boto3
import os

print("Loading function...")

def lambda_handler(event, context):
    # print("Lambda handler started")
    print("Lambda invoked")
    # print(f"Incoming event: {event}")
    try:
        
        table_name = os.environ.get("TABLE_NAME")
        print(f"Using table name: {table_name}")

        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(table_name)
        
        response = table.update_item(
            Key={"id": "visitorCount"},
            UpdateExpression="ADD #c :inc",
            ExpressionAttributeNames={"#c": "count"},
            ExpressionAttributeValues={":inc": 1},
            ReturnValues="UPDATED_NEW"
        )
        print(f"Update response: {response}")
        return {
            "statusCode": 200,
            "headers": { "Access-Control-Allow-Origin": "*" },
            "body": f"Visitor count incremented to {int(response['Attributes']['count'])}"
        }
    except Exception as e:
        print(f"Exception occurred: {e}")
        return {
            "statusCode": 500,
            "headers": { "Access-Control-Allow-Origin": "*" },
            "body": f"Error: {str(e)}"
        }
# This code is for a Lambda function that increments a visitor count in a DynamoDB table.
# It uses the AWS SDK for Python (Boto3) to interact with DynamoDB.