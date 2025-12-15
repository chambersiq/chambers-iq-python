import logging
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class DraftingLogger:
    """Comprehensive structured logging for all drafting workflow agents"""

    @staticmethod
    def log_workflow_start(workflow_id: str, case_id: str, user_id: str, template_id: Optional[str] = None):
        logger.info("Drafting workflow started", extra={
            "workflow_id": workflow_id, "case_id": case_id, "user_id": user_id,
            "template_id": template_id, "event": "workflow_start",
            "timestamp": datetime.utcnow().isoformat()
        })

    @staticmethod
    def log_agent_start(agent_name: str, workflow_id: str, section_idx: Optional[int] = None):
        logger.info(f"Agent {agent_name} started", extra={
            "agent_name": agent_name, "workflow_id": workflow_id, "section_idx": section_idx,
            "event": "agent_start", "timestamp": datetime.utcnow().isoformat()
        })

    @staticmethod
    def log_agent_end(agent_name: str, workflow_id: str, status: str = "success",
                     duration_ms: Optional[int] = None, section_idx: Optional[int] = None):
        logger.info(f"Agent {agent_name} completed", extra={
            "agent_name": agent_name, "workflow_id": workflow_id, "status": status,
            "duration_ms": duration_ms, "section_idx": section_idx,
            "event": "agent_end", "timestamp": datetime.utcnow().isoformat()
        })

    @staticmethod
    def log_llm_call(workflow_id: str, agent_name: str, model: str,
                    prompt_tokens: int, completion_tokens: int, total_tokens: int,
                    duration_ms: int, cache_read_tokens: int = 0, cache_write_tokens: int = 0,
                    section_idx: Optional[int] = None):
        logger.info("LLM API call", extra={
            "workflow_id": workflow_id, "agent_name": agent_name, "model": model,
            "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens,
            "total_tokens": total_tokens, "cache_read_tokens": cache_read_tokens,
            "cache_write_tokens": cache_write_tokens, "duration_ms": duration_ms,
            "cache_savings_percent": round((cache_read_tokens / total_tokens) * 100, 1) if cache_read_tokens > 0 else 0,
            "section_idx": section_idx, "event": "llm_call",
            "timestamp": datetime.utcnow().isoformat()
        })

    @staticmethod
    def log_planner_output(workflow_id: str, sections_count: int, total_word_estimate: int,
                          required_facts: List[str], required_laws: List[str]):
        logger.info("Planning completed", extra={
            "workflow_id": workflow_id, "sections_count": sections_count,
            "total_word_estimate": total_word_estimate, "required_facts": required_facts,
            "required_laws": required_laws, "event": "planner_output",
            "timestamp": datetime.utcnow().isoformat()
        })

    @staticmethod
    def log_context_loaded(workflow_id: str, case_id: str, template_id: Optional[str],
                          documents_count: int, facts_count: int):
        logger.info("Context loaded", extra={
            "workflow_id": workflow_id, "case_id": case_id, "template_id": template_id,
            "documents_count": documents_count, "facts_count": facts_count,
            "event": "context_loaded", "timestamp": datetime.utcnow().isoformat()
        })

    @staticmethod
    def log_citation_research(workflow_id: str, query: str, results_count: int,
                             duration_ms: int, section_idx: Optional[int] = None):
        logger.info("Citation research completed", extra={
            "workflow_id": workflow_id, "query": query, "results_count": results_count,
            "duration_ms": duration_ms, "section_idx": section_idx,
            "event": "citation_research", "timestamp": datetime.utcnow().isoformat()
        })

    @staticmethod
    def log_section_progress(workflow_id: str, section_idx: int, section_title: str, status: str):
        """Log section completion progress."""
        logger.info(f"Section {section_idx + 1} '{section_title}': {status}", extra={
            "workflow_id": workflow_id, "section_idx": section_idx, "section_title": section_title,
            "status": status, "event": "section_progress",
            "timestamp": datetime.utcnow().isoformat()
        })

    @staticmethod
    def log_writer_output(workflow_id: str, section_idx: int, section_title: str,
                         word_count: int, facts_used: int, citations_used: int,
                         placeholders_filled: Dict[str, str]):
        logger.info(f"Section {section_idx + 1} drafted", extra={
            "workflow_id": workflow_id, "section_idx": section_idx, "section_title": section_title,
            "word_count": word_count, "facts_used": facts_used, "citations_used": citations_used,
            "placeholders_filled": placeholders_filled, "event": "writer_output",
            "timestamp": datetime.utcnow().isoformat()
        })

    @staticmethod
    def log_reviewer_feedback(workflow_id: str, section_idx: int, verdict: str,
                             issues_count: int, critical_issues: int, missing_facts: List[str]):
        logger.info(f"Review completed: {verdict}", extra={
            "workflow_id": workflow_id, "section_idx": section_idx, "verdict": verdict,
            "issues_count": issues_count, "critical_issues": critical_issues,
            "missing_facts": missing_facts, "event": "reviewer_feedback",
            "timestamp": datetime.utcnow().isoformat()
        })

    @staticmethod
    def log_fact_resolution(workflow_id: str, resolved_count: int,
                           ai_inference_count: int, human_needed_count: int):
        logger.info("Fact resolution completed", extra={
            "workflow_id": workflow_id, "resolved_count": resolved_count,
            "ai_inference_count": ai_inference_count, "human_needed_count": human_needed_count,
            "event": "fact_resolution", "timestamp": datetime.utcnow().isoformat()
        })

    @staticmethod
    def log_assembler_output(workflow_id: str, total_sections: int, total_words: int,
                            final_document_size: int):
        logger.info("Document assembled", extra={
            "workflow_id": workflow_id, "total_sections": total_sections,
            "total_words": total_words, "final_document_size": final_document_size,
            "event": "assembler_output", "timestamp": datetime.utcnow().isoformat()
        })

    @staticmethod
    def log_refiner_changes(workflow_id: str, changes_made: List[str],
                           consistency_improvements: int, language_enhancements: int):
        logger.info("Document refined", extra={
            "workflow_id": workflow_id, "changes_made": changes_made,
            "consistency_improvements": consistency_improvements,
            "language_enhancements": language_enhancements, "event": "refiner_output",
            "timestamp": datetime.utcnow().isoformat()
        })

    @staticmethod
    def log_error(workflow_id: str, agent_name: str, error_type: str, error_message: str,
                 section_idx: Optional[int] = None, stack_trace: Optional[str] = None):
        logger.error(f"Error in {agent_name}: {error_message}", extra={
            "workflow_id": workflow_id, "agent_name": agent_name, "error_type": error_type,
            "error_message": error_message, "section_idx": section_idx,
            "stack_trace": stack_trace, "event": "error",
            "timestamp": datetime.utcnow().isoformat()
        }, exc_info=True)

    @staticmethod
    def log_workflow_end(workflow_id: str, status: str, duration_ms: int,
                        sections_completed: int, errors: list = None):
        logger.info("Workflow completed", extra={
            "workflow_id": workflow_id, "status": status, "duration_ms": duration_ms,
            "sections_completed": sections_completed, "errors": errors or [],
            "event": "workflow_end", "timestamp": datetime.utcnow().isoformat()
        })

# Global instance
drafting_logger = DraftingLogger()
