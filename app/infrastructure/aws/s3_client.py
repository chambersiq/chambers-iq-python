import boto3
from botocore.exceptions import ClientError
from app.core.config import settings

class S3Client:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(S3Client, cls).__new__(cls)
            cls._instance.client = boto3.client(
                "s3",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
        return cls._instance

    def generate_presigned_url(self, object_name: str, expiration: int = 3600, method: str = 'put_object'):
        try:
            response = self.client.generate_presigned_url(
                ClientMethod=method,
                Params={
                    'Bucket': settings.S3_BUCKET_NAME,
                    'Key': object_name
                },
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None

s3_client = S3Client()
