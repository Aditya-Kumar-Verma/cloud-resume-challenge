import boto3
import os

def lambda_handler(event, context):
    try:
        dynamodb = boto3.resource("dynamodb")
        table_name = os.environ.get("TABLE_NAME")
        table = dynamodb.Table(table_name)
        
        response = table.get_item(Key={'id': 'visitorCount'})
        count = response['Item']['count']
        
        return {
            "statusCode": 200,
            "headers": { "Access-Control-Allow-Origin": "*" },
            "body": str(count)
            
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": { "Access-Control-Allow-Origin": "*" },
            "body": f"Error: {str(e)}"
        }