from enum import Enum
from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime

# --- Enums ---

class AgentNode(str, Enum):
    PLANNER = "draft_master_planner"
    CONTEXT = "draft_context_manager"
    WRITER = "draft_writer"
    REVIEWER = "draft_reviewer"
    CITATION = "draft_citation_agent"
    ASSEMBLER = "draft_assembler"
    REFINER = "draft_refiner"
    HUMAN = "human_review"

class SectionStatus(str, Enum):
    PENDING = "pending"
    DRAFTING = "drafting"
    REVIEW_PENDING = "review_pending"
    APPROVED = "approved"
    NEEDS_REVISION = "needs_revision"

class QAStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"

# --- Models ---

class Section(BaseModel):
    id: str = Field(..., description="Unique ID for the section")
    title: str = Field(..., description="Human-readable title")
    template_text: str = Field(..., description="Raw template text with placeholders")
    required_facts: List[str] = Field(default_factory=list, description="List of fact keys needed")
    required_laws: List[str] = Field(default_factory=list, description="List of law topics needed")
    dependencies: List[str] = Field(default_factory=list, description="IDs of sections this depends on")
    status: SectionStatus = Field(default=SectionStatus.PENDING)
    order_index: int = Field(..., description="Position in the final document")

class DraftingPlan(BaseModel):
    sections: List[Section]
    total_estimated_sections: int
    complexity: str # "Low", "Medium", "High"

class FactEntry(BaseModel):
    key: str
    value: Any
    source_document: str # Filename or Doc ID
    source_page: Optional[int] = None
    confidence: float
    used_in_sections: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)

class Citation(BaseModel):
    text: str
    source: str # e.g. "Indian Kanoon"
    url: Optional[str] = None
    case_name: Optional[str] = None
    year: Optional[int] = None

class DraftedSection(BaseModel):
    section_id: str
    content: str
    facts_used: List[str] # List of FactEntry keys
    citations_used: List[Citation]
    placeholders_filled: Dict[str, str]
    word_count: int

class Issue(BaseModel):
    type: str  # "missing_fact", "inconsistency", "legal_error", "style"
    description: str
    location: Optional[str] = None
    severity: str # "Critical", "Warning", "Info"
    suggested_fix: Optional[str] = None

class QAReport(BaseModel):
    section_id: str
    status: QAStatus
    issues: List[Issue] = Field(default_factory=list)
    recommendation: str

class RefinementPlan(BaseModel):
    section_id: str
    refinement_type: str # "factual", "legal", "style", "structure"
    issues_to_fix: List[str] 
    routed_to: AgentNode # Which agent handles this?
    instructions: str
