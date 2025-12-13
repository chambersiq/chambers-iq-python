from typing import Literal, Dict, Any, Optional
from app.agents.workflows.drafting.state import DraftState
from app.agents.workflows.drafting.schema import QAStatus, AgentNode

from app.agents.workflows.drafting.config import drafting_config

class WorkflowRouter:
    """
    Centralized routing logic for the Drafting Workflow.
    Decouples conditional logic from the graph definition.
    """
    
    def __init__(self):
        self.config = drafting_config

    def route_after_review(self, state: DraftState) -> Literal["prepare_redraft", "increment_section", "human_review_section", "smart_resolution"]:
        """
        Decide next step after QA Review:
        - FAIL + Missing Info -> Smart Resolution
        - FAIL (Quality) -> Redraft (up to limit) -> Human Review
        - PASS -> Store & Continue
        """
        report = state.get("current_qa_report")
        current_section = state.get("current_section")
        section_redraft_count = state.get("section_redraft_count", 0)
        
        # Check for missing info (Ground Truth from draft + Critical Issues)
        missing_info_detected = False
        
        # 1. Draft Content Markers
        if current_section and state.get("current_draft"):
            content = state["current_draft"].content
            if "[MISSING:" in content:
                missing_info_detected = True
                print("  ⚠️  Draft contains [MISSING: ...] markers -> Flagged for Smart Resolution")

        # 2. Critical Report Issues
        if not missing_info_detected and report:
            for issue in report.issues:
                if issue.severity == "Critical":
                    desc = issue.description.lower()
                    if "missing" in desc or "provide" in desc or "not provided" in desc:
                        missing_info_detected = True
                        print(f"  ⚠️  Critical issue indicates missing info: '{issue.description}' -> Flagged for Smart Resolution")
                        break

        # PRIORITY 0: Check Hard Loop Limits First
        # If we exceeded the limit, we MUST stop or force human review, even if info is missing.
        if section_redraft_count >= self.config.MAX_SECTION_REDRAFTS:
             print(f"  ⚠️  Autonomous limit reached ({section_redraft_count}). Requesting Human intervention.")
             return "human_review_section"

        if missing_info_detected:
             print(f"  ⚠️  Missing information detected (markers or critical issues). Routing to Smart Resolution.")
             return "smart_resolution"

        if report and report.status == QAStatus.FAIL:
            # PRIORITY 1: Missing Data -> Handled above

            # PRIORITY 2: Quality/Style Issues -> Retry Logic
            # We already checked MAX limit above. If we are here, we are under the limit.
            print(f"  → Routing to prepare_redraft (current count: {section_redraft_count}, max: {self.config.MAX_SECTION_REDRAFTS})")
            return "prepare_redraft"

        # PASS / PASS_WITH_WARNINGS
        print(f"  → Section approved, moving to next")
        return "increment_section"

    def route_resolution(self, state: DraftState) -> Literal["prepare_redraft", "human_review_section"]:
        """
        Decide next step after Smart Resolution.
        """
        result = state.get("resolution_result")
        section_redraft_count = state.get("section_redraft_count", 0)

        # CRITICAL: Check counter even after resolution
        if section_redraft_count >= self.config.MAX_SECTION_REDRAFTS:
            print(f"  ⚠️  Loop limit reached ({section_redraft_count}). Forcing human review.")
            return "human_review_section"

        if not result:
            return "human_review_section"

        if not result.human_input_needed:
            print("  ✓ Smart Resolution SUCCESS. Looping back to Writer.")
            return "prepare_redraft"

        print(f"  ? Smart Resolution Incomplete. {len(result.human_input_needed)} keys need human.")
        return "human_review_section"

    def route_after_section_human_review(self, state: DraftState) -> Literal["increment_section", "prepare_redraft"]:
        """
        Route based on human verdict for a section loop.
        """
        verdict = state.get("human_verdict")
        print(f"--- [HumanReview] Verdict received: {verdict} ---")
        
        if verdict == "approve":
            return "increment_section"
        
        # refine or reject -> fix it
        return "prepare_redraft"

    def route_after_increment(self, state: DraftState) -> Literal["writer", "refiner", "human"]:
        """
        Check if more sections remain or if complete.
        """
        plan = state.get("plan")
        current_idx = state.get("current_section_idx", 0)

        if not plan:
            return AgentNode.HUMAN # Error case

        total_sections = len(plan.sections)

        if current_idx >= total_sections:
            print(f"--- [WorkflowComplete] All {total_sections} sections drafted! Moving to final refiner ---")
            return AgentNode.REFINER
        else:
            print(f"--- [NextSection] Moving to section {current_idx + 1}/{total_sections} ---")
            return AgentNode.WRITER

# Singleton instance for now
router = WorkflowRouter()
