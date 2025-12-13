import sys
import os
import boto3
from typing import List, Dict

# Ensure app modules can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.repositories.case_repository import CaseRepository
from app.repositories.template_repository import TemplateRepository
from app.core.config import settings

def migrate_cases():
    print("Migrating Cases...")
    repo = CaseRepository()
    table = repo.table
    
    # 1. Scan all cases
    response = table.scan()
    items = response.get('Items', [])
    
    updates_count = 0
    
    # Mappings (Example - normally would load from master-data.json or hardcoded common ones)
    LEGACY_MAP = {
        'civil-litigation': {'caseTypeId': 'CT_CIV_01', 'practiceArea': 'Civil Litigation'},
        'criminal-defense': {'caseTypeId': 'CT_CRM_01', 'practiceArea': 'Criminal Defense'},
        'family-law': {'caseTypeId': 'CT_FAM_01', 'practiceArea': 'Family Law'},
        'corporate-law': {'caseTypeId': 'CT_CORP_01', 'practiceArea': 'Corporate Law'},
    }
    
    for item in items:
        case_id = item.get('caseId')
        company_id = item.get('companyId')
        
        if not case_id or not company_id:
            continue
            
        legacy_type = item.get('caseType')
        current_cat = item.get('caseTypeId')
        
        if not current_cat and legacy_type in LEGACY_MAP:
            mapping = LEGACY_MAP[legacy_type]
            print(f"Updating Case {case_id} ({legacy_type}) -> {mapping['caseTypeId']}")
            
            # Direct update to avoid overhead
            table.update_item(
                Key={'companyId': company_id, 'caseId': case_id},
                UpdateExpression="SET caseTypeId = :ct, practiceArea = :pa",
                ExpressionAttributeValues={
                    ':ct': mapping['caseTypeId'],
                    ':pa': mapping['practiceArea']
                }
            )
            updates_count += 1
            
    print(f"Cases Updated: {updates_count}")

def migrate_templates():
    print("Migrating Templates...")
    repo = TemplateRepository()
    table = repo.table
    
    response = table.scan()
    items = response.get('Items', [])
    updates_count = 0
    
    # Simple Heuristic Map for Templates
    CATEGORY_MAP = {
        'pleading': 'DT_PL_01', # Plaint
        'contract': 'DT_CON_01', # Agreement
    }
    
    for item in items:
        # Templates PK is companyId, SK is caseType#templateId
        # We need full keys
        company_id = item.get('companyId')
        sk = item.get('caseType#templateId') # This matches how it's stored in DynamoDB based on Repo
        # Wait, Repo define delete using "caseType#templateId". But create uses save(item).
        # We need to verify the actual table schema or just use what we scanned.
        # If we scanned, we have the item.
        
        # Actually TemplateRepo uses BaseRepository connected to DYNAMODB_TABLE_TEMPLATES.
        # The key schema is PK=companyId, SK=templateId (Wait, check repo delete: caseType#templateId?)
        # Let's check repository code I viewed earlier.
        # TemplateRepo.delete used "caseType#templateId".
        # This implies SK is composite.
        # But get_by_id_global uses Filter scan on templateId.
        
        # If SK is caseType#templateId, we need that key.
        # Scan returns it.
        
        if not company_id: 
            continue
            
        # Determine SK key name. It's likely "caseType#templateId" if stored that way, OR "templateId" if I misread delete method.
        # Let's assume standard "templateId" if delete was legacy or specific GSI usage.
        # Actually, let's look at `item` keys.
        # Safest is to check common keys.
        
        # Assuming table is standard PK/SK.
        pass

from app.repositories.document_repository import DocumentRepository
from app.repositories.draft_repository import DraftRepository

def migrate_documents():
    print("Migrating Documents...")
    repo = DocumentRepository()
    table = repo.table
    
    response = table.scan()
    items = response.get('Items', [])
    updates_count = 0
    
    # Generic Map based on legacy constants
    DOC_MAP = {
        'pleading': {'id': 'DT_PL_01', 'cat': 'DC_PL_01'}, # Plaint in Civil
        'motion': {'id': 'DT_APP_01', 'cat': 'DC_APP_01'}, # Application
        'evidence': {'id': 'DT_AFF_01', 'cat': 'DC_EVD_01'}, # Affidavit
        'contract': {'id': 'DT_CON_01', 'cat': 'DC_CON_01'}, # Agreement
        'letter': {'id': 'DT_OTH_01', 'cat': 'DC_OTH_01'}, # Other
        'other': {'id': 'DT_OTH_01', 'cat': 'DC_OTH_01'},
    }
    
    for item in items:
        # Document PK is companyId (Repository uses companyId), SK: documentId
        # The item scan returns attributes. We should use companyId if available.
        company_id = item.get('companyId')
        doc_id = item.get('documentId')
        
        if not company_id or not doc_id:
            # Fallback: maybe parentId is used as companyId in some data?
            # But repository confirms Key={"companyId": ...}
            continue
            
        legacy_type = item.get('documentType', 'other') 
        
        if 'documentTypeId' not in item:
             table.update_item(
                Key={'companyId': company_id, 'documentId': doc_id},
                UpdateExpression="SET documentTypeId = :dt, documentCategoryId = :dc",
                ExpressionAttributeValues={
                    ':dt': 'DT_OTH_01',
                    ':dc': 'DC_OTH_01'
                }
            )
             updates_count += 1

    print(f"Documents Updated: {updates_count}")

def migrate_drafts():
    print("Migrating Drafts...")
    repo = DraftRepository()
    table = repo.table
    
    response = table.scan()
    items = response.get('Items', [])
    updates_count = 0
    
    for item in items:
        case_id = item.get('caseId')
        draft_id = item.get('draftId')
        
        if not case_id or not draft_id:
            continue
            
        if 'documentTypeId' not in item:
             table.update_item(
                Key={'caseId': case_id, 'draftId': draft_id},
                UpdateExpression="SET documentTypeId = :dt, documentCategoryId = :dc",
                ExpressionAttributeValues={
                    ':dt': 'DT_OTH_01',
                    ':dc': 'DC_OTH_01'
                }
            )
             updates_count += 1
             
    print(f"Drafts Updated: {updates_count}")

if __name__ == "__main__":
    migrate_cases()
    migrate_documents()
    migrate_drafts()
    # migrate_templates()
