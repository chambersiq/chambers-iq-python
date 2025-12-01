import boto3
from app.core.config import settings

def create_users_table():
    dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
    table_name = settings.DYNAMODB_TABLE_USERS
    
    print(f"Creating table: {table_name}")
    
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'email', 'KeyType': 'HASH'}  # Partition key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'email', 'AttributeType': 'S'},
                {'AttributeName': 'companyId', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'by_company',
                    'KeySchema': [
                        {'AttributeName': 'companyId', 'KeyType': 'HASH'}
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
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
    create_users_table()
