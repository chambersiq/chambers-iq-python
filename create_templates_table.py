import boto3
from app.core.config import settings

def create_templates_table():
    dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
    table_name = settings.DYNAMODB_TABLE_TEMPLATES
    
    print(f"Creating table: {table_name}")
    
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'companyId', 'KeyType': 'HASH'},  # Partition key
                {'AttributeName': 'caseType#templateId', 'KeyType': 'RANGE'}  # Sort key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'companyId', 'AttributeType': 'S'},
                {'AttributeName': 'caseType#templateId', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print("Table status:", table.table_status)
        table.wait_until_exists()
        print("Table created successfully!")
    except Exception as e:
        print(f"Error creating table: {e}")

if __name__ == "__main__":
    create_templates_table()
