from typing import List, Optional
import uuid
from datetime import datetime
import boto3
from app.core.config import settings
from app.repositories.template_repository import TemplateRepository
from app.infrastructure.aws.s3_client import S3Client
from app.api.v1.schemas.template import Template, TemplateCreate

class TemplateService:
    def __init__(self):
        self.repo = TemplateRepository()
        self.s3 = S3Client()

    def create_template(self, company_id: str, data: TemplateCreate, created_by: str = "Unknown") -> Template:
        template_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        # Use createdBy from data if provided, otherwise use argument
        final_created_by = data.createdBy if data.createdBy else created_by
        
        # Upload content to S3
        s3_key = f"{company_id}/templates/{template_id}.html"
        try:
            print(f"Uploading template content to S3: {settings.S3_BUCKET_NAME}/{s3_key}")
            self.s3.client.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=s3_key,
                Body=data.content.encode('utf-8'),
                ContentType='text/html'
            )
            print("Upload successful")
        except Exception as e:
            print(f"Error uploading template to S3: {e}")
            # For now, we'll raise the error to see it in the 500 response logs if possible,
            # or we can let it bubble up. But printing it helps if we can see stdout.
            raise e
        
        template_dict = data.model_dump()
        template_dict.update({
            "companyId": company_id,
            "templateId": template_id,
            "caseType#templateId": f"{data.category}#{template_id}", # Construct SK
            "s3Key": s3_key,
            "createdAt": now,
            "updatedAt": now,
            "createdBy": final_created_by
        })
        
        # Remove content from dict before saving to DynamoDB (optional, but cleaner)
        # But we keep it in the returned object
        db_item = template_dict.copy()
        del db_item['content']
        
        self.repo.create(db_item)
        return Template(**template_dict)

    def get_templates(self, company_id: str) -> List[Template]:
        # Query by PK only (companyId)
        items = self.repo.get_all_for_company(company_id)
        # We don't fetch content for list view to save bandwidth
        # Ensure we don't pass content twice if it exists in item
        templates = []
        for item in items:
            item_data = {k: v for k, v in item.items() if k != 'content'}
            templates.append(Template(**item_data, content=""))
        return templates

    def get_template(self, company_id: str, template_id: str) -> Optional[Template]:
        item = self.repo.get_by_id_global(template_id)
        if not item:
            return None
            
        # Fetch content from S3
        content = ""
        if item.get("s3Key"):
            try:
                response = self.s3.client.get_object(Bucket=settings.S3_BUCKET_NAME, Key=item["s3Key"])
                content = response['Body'].read().decode('utf-8')
            except Exception as e:
                print(f"Error fetching template content from S3: {e}")
                
        return Template(**item, content=content)
