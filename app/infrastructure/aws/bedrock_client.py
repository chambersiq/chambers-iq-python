import boto3
import json
from app.core.config import settings

class BedrockClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BedrockClient, cls).__new__(cls)
            cls._instance.client = boto3.client(
                "bedrock-runtime",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
        return cls._instance

    async def invoke_model(self, prompt: str, max_tokens: int = 1000):
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}]
                }
            ]
        })

        try:
            response = self.client.invoke_model(
                body=body,
                modelId=settings.BEDROCK_MODEL_ID,
                accept="application/json",
                contentType="application/json",
            )
            response_body = json.loads(response.get("body").read())
            return response_body.get("content")[0].get("text")
        except Exception as e:
            print(f"Error invoking Bedrock: {e}")
            raise e

bedrock_client = BedrockClient()
