from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

class Party(BaseModel):
    name: str
    type: str  # Updated to accept Master Data IDs (e.g., PT_01)
    address: Optional[str] = None # Added field
    opposingCounselName: Optional[str] = None
    opposingCounselFirm: Optional[str] = None
    opposingCounselEmail: Optional[str] = None
    opposingCounselPhone: Optional[str] = None

class ImportantDate(BaseModel):
    id: Optional[str] = None
    name: str
    date: str
    description: Optional[str] = None
    reminderDays: Optional[int] = None

from enum import Enum

class CaseStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DISCOVERY = "discovery"
    MOTION_PRACTICE = "motion-practice"
    TRIAL = "trial"
    SETTLEMENT = "settlement"
    CLOSED = "closed"
    ON_HOLD = "on-hold"


class CasePriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class FeeArrangement(str, Enum):
    HOURLY = "hourly"
    CONTINGENCY = "contingency"
    FLAT_FEE = "flat-fee"
    HYBRID = "hybrid"
    PRO_BONO = "pro-bono"

class CaseBase(BaseModel):
    # Basic Info
    caseNumber: Optional[str] = None
    caseName: str
    # caseType removed
    caseSubType: Optional[str] = None
    status: CaseStatus = CaseStatus.ACTIVE

    # Case Summary
    caseSummary: Optional[str] = None
    clientPosition: Optional[str] = None
    opposingPartyPosition: Optional[str] = None
    keyFacts: Optional[List[str]] = []
    legalIssues: Optional[str] = None
    prayer: Optional[str] = None # Formerly desiredOutcome
    caseStrategyNotes: Optional[str] = None

    # Case Details
    jurisdiction: Optional[str] = None
    courtLevelId: Optional[str] = None # Added for Phase 2
    caseTypeId: Optional[str] = None # Added for Phase 2
    practiceArea: Optional[str] = None # Added for Phase 2
    primaryStatuteId: Optional[str] = None # Added for Phase 2
    limitationYears: Optional[int] = None # Added for Phase 2
    allowedDocTypeIds: List[str] = [] # Added for Phase 2
    reliefIds: List[str] = [] # Added for Phase 2
    
    venue: Optional[str] = None
    courtName: Optional[str] = None
    department: Optional[str] = None
    judgeName: Optional[str] = None
    caseFiledDate: Optional[str] = None
    docketNumber: Optional[str] = None

    # Parties
    opposingPartyName: Optional[str] = None
    opposingPartyType: Optional[str] = None # Changed from Literal to str to accept IDs
    opposingCounselName: Optional[str] = None
    opposingCounselFirm: Optional[str] = None
    opposingCounselEmail: Optional[str] = None
    opposingCounselPhone: Optional[str] = None
    additionalParties: Optional[List[Party]] = []

    # Important Dates
    statuteOfLimitationsDate: Optional[str] = None
    nextHearingDate: Optional[str] = None
    trialDate: Optional[str] = None
    discoveryCutoff: Optional[str] = None
    motionFilingDeadlines: Optional[List[ImportantDate]] = []
    mediationDate: Optional[str] = None
    settlementConferenceDate: Optional[str] = None
    customDeadlines: Optional[List[ImportantDate]] = []

    # Financial
    estimatedCaseValue: Optional[float] = None
    clientDamagesClaimed: Optional[float] = None
    feeArrangement: Optional[FeeArrangement] = None
    contingencyFeePercent: Optional[float] = None
    hourlyBillingRate: Optional[float] = None
    flatFeeAmount: Optional[float] = None
    retainerAmount: Optional[float] = None
    budgetEstimate: Optional[float] = None
    costsAdvanced: Optional[float] = None

    # Additional
    priority: CasePriority = CasePriority.MEDIUM
    caseSource: Optional[str] = None
    conflictCheckStatus: Optional[str] = None
    tags: Optional[List[str]] = []
    caseNotes: Optional[str] = None
    relatedCaseIds: Optional[List[str]] = []
    archived: bool = False

class CaseCreate(CaseBase):
    pass

class Case(CaseBase):
    companyId: str
    clientId: str
    caseId: str
    clientName: Optional[str] = None # Denormalized
    createdAt: str
    updatedAt: str
    createdBy: Optional[str] = None
