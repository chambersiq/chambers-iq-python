from typing import Optional, List
import uuid
from datetime import datetime
from app.repositories.company_repository import CompanyRepository, UserRepository
from app.api.v1.schemas.company import Company, CompanyCreate, User, UserCreate

class CompanyService:
    def __init__(self):
        self.company_repo = CompanyRepository()
        self.user_repo = UserRepository()

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

class UserService:
    def __init__(self):
        self.user_repo = UserRepository()

    def create_user(self, company_id: str, data: UserCreate) -> User:
        # Check if exists globally (email is PK)
        if self.user_repo.get_by_email_global(data.email):
            raise ValueError("User email already exists")

        user = User(
            **data.model_dump(),
            companyId=company_id,
            userId=str(uuid.uuid4()),
            status="active",
            createdAt=datetime.utcnow().isoformat()
        )
        self.user_repo.create(user.model_dump())
        return user

    def get_users(self, company_id: str) -> List[User]:
        items = self.user_repo.get_all_for_company(company_id)
        return [User(**item) for item in items]

    def get_user_by_email_global(self, email: str) -> Optional[User]:
        item = self.user_repo.get_by_email_global(email)
        return User(**item) if item else None
