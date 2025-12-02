from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # AWS Configuration
    AWS_REGION: str = "ap-south-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    
    # DynamoDB Tables (Defaults matching CDK)
    DYNAMODB_TABLE_COMPANIES: str = "chambers-iq-beta-companies"
    DYNAMODB_TABLE_USERS: str = "chambers-iq-beta-users"
    DYNAMODB_TABLE_CLIENTS: str = "chambers-iq-beta-clients"
    DYNAMODB_TABLE_CASES: str = "chambers-iq-beta-cases"
    DYNAMODB_TABLE_DOCUMENTS: str = "chambers-iq-beta-documents"
    DYNAMODB_TABLE_TEMPLATES: str = "chambers-iq-beta-templates"
    DYNAMODB_TABLE_DRAFTS: str = "chambers-iq-beta-drafts"
    
    # S3 Bucket
    S3_BUCKET_NAME: str
    
    # AI Services
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Chambers IQ API"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://chambers-iq-frontend-production.up.railway.app"
    ]
    
    # Feature Flags
    ENABLE_AI_DRAFTING: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
