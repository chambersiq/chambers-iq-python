"""
Loop prevention mechanisms for the drafting workflow.

Prevents infinite loops by:
1. Tracking iteration counts per section
2. Enforcing maximum revision attempts
3. Detecting cyclic patterns
4. Implementing circuit breakers
"""

from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict

class LoopPreventor:
    """Prevents infinite loops in the drafting workflow."""

    def __init__(
        self,
        max_total_iterations: int = 10,
        max_section_revisions: int = 3,
        max_writer_reviewer_cycles: int = 2
    ):
        """
        Initialize loop prevention.

        Args:
            max_total_iterations: Maximum total workflow iterations
            max_section_revisions: Maximum revisions per section
            max_writer_reviewer_cycles: Maximum Writer→Reviewer cycles before human intervention
        """
        self.max_total_iterations = max_total_iterations
        self.max_section_revisions = max_section_revisions
        self.max_writer_reviewer_cycles = max_writer_reviewer_cycles

        # Tracking
        self.section_revision_counts: Dict[str, int] = defaultdict(int)
        self.section_history: Dict[str, List[str]] = defaultdict(list)
        self.writer_reviewer_cycle_count: int = 0

    def check_total_iterations(self, current_count: int) -> tuple[bool, Optional[str]]:
        """
        Check if total iterations exceeded.

        Returns:
            (is_allowed, error_message)
        """
        if current_count >= self.max_total_iterations:
            return False, (
                f"Maximum total iterations ({self.max_total_iterations}) reached. "
                "Workflow terminated to prevent infinite loop. "
                "Please review the case requirements or template."
            )
        return True, None

    def check_section_revisions(self, section_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if section revision limit exceeded.

        Returns:
            (is_allowed, error_message)
        """
        count = self.section_revision_counts[section_id]

        if count >= self.max_section_revisions:
            return False, (
                f"Section has been revised {count} times (max: {self.max_section_revisions}). "
                "Forcing human review to break the loop. "
                "The section may have fundamental issues requiring human judgment."
            )
        return True, None

    def increment_section_revision(self, section_id: str, status: str):
        """
        Track a section revision attempt.

        Args:
            section_id: ID of the section
            status: Status from QA (PASS, FAIL, PASS_WITH_WARNINGS)
        """
        self.section_revision_counts[section_id] += 1
        self.section_history[section_id].append(status)

        print(f"  [LoopPrevention] Section {section_id[:8]}... revision count: "
              f"{self.section_revision_counts[section_id]}/{self.max_section_revisions}")

    def check_writer_reviewer_cycle(self) -> tuple[bool, Optional[str]]:
        """
        Check if Writer→Reviewer cycle limit exceeded.

        Returns:
            (is_allowed, error_message)
        """
        if self.writer_reviewer_cycle_count >= self.max_writer_reviewer_cycles:
            return False, (
                f"Writer→Reviewer cycle repeated {self.writer_reviewer_cycle_count} times "
                f"(max: {self.max_writer_reviewer_cycles}). "
                "Forcing human review. The draft may need significant changes that require human judgment."
            )
        return True, None

    def increment_writer_reviewer_cycle(self):
        """Track a Writer→Reviewer cycle."""
        self.writer_reviewer_cycle_count += 1
        print(f"  [LoopPrevention] Writer→Reviewer cycle: "
              f"{self.writer_reviewer_cycle_count}/{self.max_writer_reviewer_cycles}")

    def reset_writer_reviewer_cycle(self):
        """Reset cycle count (called when section is approved or changed)."""
        self.writer_reviewer_cycle_count = 0

    def detect_cyclic_pattern(self, section_id: str) -> tuple[bool, Optional[str]]:
        """
        Detect if section is stuck in a cyclic pattern.

        Example: FAIL → FAIL → FAIL (same issues repeatedly)

        Returns:
            (has_pattern, warning_message)
        """
        history = self.section_history[section_id]

        if len(history) < 3:
            return False, None

        # Check if last 3 attempts all failed
        if history[-3:] == ["FAIL", "FAIL", "FAIL"]:
            return True, (
                f"Section appears stuck in a failure loop (3 consecutive FAILs). "
                "This suggests a fundamental issue with available facts or template. "
                "Recommend human intervention."
            )

        return False, None

    def get_stats(self) -> Dict:
        """Get loop prevention statistics."""
        return {
            "total_sections_revised": len(self.section_revision_counts),
            "sections_at_limit": sum(
                1 for count in self.section_revision_counts.values()
                if count >= self.max_section_revisions
            ),
            "writer_reviewer_cycles": self.writer_reviewer_cycle_count,
            "section_revision_counts": dict(self.section_revision_counts)
        }

def check_workflow_health(state: dict, loop_preventor: LoopPreventor) -> tuple[bool, Optional[str]]:
    """
    Comprehensive workflow health check.

    Returns:
        (is_healthy, error_message)
    """
    # Check 1: Total iterations
    iteration_count = state.get("iteration_count", 0)
    is_ok, error = loop_preventor.check_total_iterations(iteration_count)
    if not is_ok:
        return False, error

    # Check 2: Section revisions (if current section exists)
    current_section = state.get("current_section")
    if current_section:
        section_id = current_section.id
        is_ok, error = loop_preventor.check_section_revisions(section_id)
        if not is_ok:
            return False, error

        # Check 3: Cyclic pattern detection
        has_pattern, warning = loop_preventor.detect_cyclic_pattern(section_id)
        if has_pattern:
            return False, warning

    # Check 4: Writer→Reviewer cycles
    is_ok, error = loop_preventor.check_writer_reviewer_cycle()
    if not is_ok:
        return False, error

    return True, None
