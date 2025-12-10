from typing import Optional, List
import uuid
from datetime import datetime, timedelta
from app.repositories.company_repository import CompanyRepository, UserRepository
from app.repositories.client_repository import ClientRepository
from app.repositories.case_repository import CaseRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.draft_repository import DraftRepository
from app.api.v1.schemas.company import Company, CompanyCreate, User, UserCreate

class CompanyService:
    def __init__(self):
        self.company_repo = CompanyRepository()
        self.user_repo = UserRepository()
        self.client_repo = ClientRepository()
        self.case_repo = CaseRepository()
        self.document_repo = DocumentRepository()
        self.draft_repo = DraftRepository()

    def create_company(self, data: CompanyCreate) -> Company:
        # Check if exists
        if self.company_repo.get_by_id(data.companyId):
            raise ValueError("Company ID already exists")

        company = Company(
            **data.model_dump(),
            status="active",
            createdAt=datetime.utcnow().isoformat()
        )
        self.company_repo.create(company.model_dump())
        return company

    def get_company(self, company_id: str) -> Optional[Company]:
        item = self.company_repo.get_by_id(company_id)
        return Company(**item) if item else None

    def get_dashboard_stats(self, company_id: str) -> dict:
        now = datetime.utcnow()
        week_ago = (now - timedelta(days=7)).isoformat()
        month_ago = (now - timedelta(days=30)).isoformat()
        
        # Get Deadlines
        cases = self.case_repo.get_all_for_company(company_id)
        deadlines = []
        
        for case in cases:
            case_name = case.get('caseName', 'Unknown Case')
            case_id = case.get('caseId')
            
            # Helper to add deadline
            def add_date(date_str, title, type_):
                # Include deadlines from last 60 days (to show recent/overdue) up to future
                # The user might have test data in recent past
                filter_date = (now - timedelta(days=60)).strftime("%Y-%m-%d")
                
                if date_str and date_str >= filter_date:
                    deadlines.append({
                        "id": f"{case_id}-{type_}-{date_str}", 
                        "title": f"{title} - {case_name}",
                        "date": date_str,
                        "type": type_
                    })

            # Check standard dates
            add_date(case.get('statuteOfLimitationsDate'), "Statute of Limitations", "statute")
            add_date(case.get('nextHearingDate'), "Next Hearing", "hearing")
            add_date(case.get('trialDate'), "Trial Date", "trial")
            add_date(case.get('discoveryCutoff'), "Discovery Cutoff", "discovery")
            add_date(case.get('mediationDate'), "Mediation", "mediation")
            add_date(case.get('settlementConferenceDate'), "Settlement Conference", "settlement")
            
            # Check lists
            for d in case.get('motionFilingDeadlines', []):
                add_date(d.get('date'), d.get('name', 'Motion Deadline'), "motion")
                
            for d in case.get('customDeadlines', []):
                add_date(d.get('date'), d.get('name', 'Custom Deadline'), "custom")
                
        # Sort by date ASC and take top 5
        deadlines.sort(key=lambda x: x['date'])
        upcoming_deadlines = deadlines[:5]

        # Get Recent Activity
        activity = []
        
        # 1. New Clients
        recent_clients = self.client_repo.get_all_for_company(company_id, include_archived=True)
        for client in recent_clients:
            if client.get('createdAt'):
                is_deleted = client.get('archived', False)
                activity.append({
                    "id": f"client-{client.get('clientId')}",
                    "type": "client",
                    "title": "Client Deleted" if is_deleted else "New Client Added",
                    "subtitle": client.get('name', 'Unknown Client'),
                    "date": client.get('updatedAt') if is_deleted else client.get('createdAt'),
                    "user": "System"
                })

        # 2. New Cases
        recent_cases = self.case_repo.get_all_for_company(company_id, include_archived=True)
        for case in recent_cases:
            if case.get('createdAt'):
                is_deleted = case.get('archived', False)
                activity.append({
                    "id": f"case-{case.get('caseId')}",
                    "type": "case",
                    "title": "Case Deleted" if is_deleted else "New Case Created",
                    "subtitle": case.get('caseName', 'Unknown Case'),
                    "date": case.get('updatedAt') if is_deleted else case.get('createdAt'),
                    "user": "System"
                })

        # 3. Documents
        recent_docs = self.document_repo.get_all_for_company(company_id, include_archived=True)
        for doc in recent_docs:
            if doc.get('createdAt'):
                is_deleted = doc.get('archived', False)
                activity.append({
                    "id": f"doc-{doc.get('documentId')}",
                    "type": "document",
                    "title": "Document Deleted" if is_deleted else "Document Uploaded",
                    "subtitle": doc.get('name', 'Unknown Document'),
                    "date": doc.get('updatedAt') if is_deleted else doc.get('createdAt'),
                    "user": "System"
                })

        # 4. Drafts
        recent_drafts = self.draft_repo.get_all_for_company(company_id, include_archived=True)
        for draft in recent_drafts:
            if draft.get('createdAt'):
                is_deleted = draft.get('archived', False)
                activity.append({
                    "id": f"draft-{draft.get('draftId')}",
                    "type": "draft",
                    "title": "Draft Deleted" if is_deleted else "Draft Created",
                    "subtitle": draft.get('name', 'Unknown Draft'),
                    "date": draft.get('updatedAt') if is_deleted and draft.get('updatedAt') else draft.get('createdAt'), # drafts might not have updatedAt on delete in my implementation
                    "user": "AI Assistant"
                })
        
        # Sort DESC and take top 10
        activity.sort(key=lambda x: x['date'], reverse=True)
        recent_activity = activity[:10]

        return {
            "activeClients": self.client_repo.count_for_company(company_id),
            "newClientsThisMonth": self.client_repo.count_created_after(company_id, month_ago),
            "activeCases": self.case_repo.count_for_company(company_id),
            "newCasesThisWeek": self.case_repo.count_created_after(company_id, week_ago),
            "documentsProcessed": self.document_repo.count_for_company(company_id),
            "newDocumentsThisWeek": self.document_repo.count_created_after(company_id, week_ago),
            "aiDraftsCreated": self.draft_repo.count_for_company(company_id),
            "newDraftsThisWeek": self.draft_repo.count_created_after(company_id, week_ago),
            "upcomingDeadlines": upcoming_deadlines,
            "recentActivity": recent_activity
        }

class UserService:
    def __init__(self):
        self.user_repo = UserRepository()

    def create_user(self, company_id: str, data: UserCreate) -> User:
        # Check if exists globally (email is PK)
        existing = self.user_repo.get_by_email_global(data.email)
        
        if existing:
            # 1. Check Company Match
            if existing.get('companyId') != company_id:
                raise ValueError(f"User with email {data.email} already belongs to another company.")
            
            # 2. Check Archived Status
            if existing.get('archived'):
                # Reactivate
                updates = {
                    "archived": False,
                    "updatedAt": datetime.utcnow().isoformat(),
                    "status": "active" # Reset status to active
                }
                # Update attributes
                updated_item = {**existing, **updates}
                self.user_repo.create(updated_item)
                return User(**updated_item)
            else:
                raise ValueError("User email already exists")

        # Super Admin Uniqueness Check
        if data.role == 'super_admin':
            existing_users = self.user_repo.get_all_for_company(company_id)
            for u in existing_users:
                if u.get('role') == 'super_admin':
                     raise ValueError("A Super Admin already exists for this company.")

        user = User(
            **data.model_dump(),
            companyId=company_id,
            userId=str(uuid.uuid4()),
            status="active",
            createdAt=datetime.utcnow().isoformat(),
            archived=False
        )
        self.user_repo.create(user.model_dump())
        return user

    def get_users(self, company_id: str) -> List[User]:
        items = self.user_repo.get_all_for_company(company_id)
        return [User(**item) for item in items]

    def get_user_by_email_global(self, email: str) -> Optional[User]:
        item = self.user_repo.get_by_email_global(email)
        return User(**item) if item else None

    def update_user(self, email: str, data: dict) -> Optional[User]:
        # 'data' should be a dict of fields to update from UserUpdate
        
        item = self.user_repo.get_by_email_global(email)
        if not item:
            return None
            
        # Super Admin Immutability Check
        if item.get('role') == 'super_admin':
             raise ValueError("Super Admin users cannot be edited.")
        
        # Prevent elevating to Super Admin if one exists
        if data.get('role') == 'super_admin':
             # Check if trying to change to super_admin
             if item.get('role') != 'super_admin':
                 company_id = item.get('companyId')
                 existing_users = self.user_repo.get_all_for_company(company_id)
                 for u in existing_users:
                     if u.get('role') == 'super_admin':
                         raise ValueError("A Super Admin already exists for this company.")

        # Merge
        # Exclude None values from data
        updates = {k: v for k, v in data.items() if v is not None}
        updated_item = {**item, **updates, "updatedAt": datetime.utcnow().isoformat()}
        
        # Save (PutItem overwrites)
        self.user_repo.create(updated_item)
        return User(**updated_item)

    def delete_user(self, email: str, requester_email: str):
        item = self.user_repo.get_by_email_global(email)
        if not item:
            return # Idempotent

        # Security: Check same company
        requester = self.user_repo.get_by_email_global(requester_email)
        if not requester:
             raise ValueError("Requester not found")
        
        # Determine strict or loose check. 
        # Ideally, we check requester.companyId == item.companyId
        # Exceptions: Super Admin might delete others? No, super admin is per company.
        
        if requester.get('companyId') != item.get('companyId'):
            raise ValueError("Unauthorized: Cannot delete user from another company")

        if item.get('role') == 'super_admin':
            raise ValueError("Cannot delete Super Admin")
            
        self.user_repo.delete(email)
