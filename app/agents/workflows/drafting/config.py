from pydantic_settings import BaseSettings

class DraftingConfig(BaseSettings):
    """
    Centralized configuration for the Drafting Workflow.
    Replaces hardcoded magic numbers.
    """
    # Workflow Limits
    MAX_TOTAL_ITERATIONS: int = 10
    MAX_SECTION_REDRAFTS: int = 2
    MAX_WRITER_REVIEWER_CYCLES: int = 2
    
    # Intelligence Thresholds
    CONFIDENCE_THRESHOLD: float = 0.8
    MIN_FACT_CONFIDENCE: float = 0.6 # Warn if below this
    
    # Context Management
    Initial_DOC_LIMIT: int = 5
    MAX_CONTEXT_TOKENS: int = 16000 # Default context window safe limit
    
    # System Prompts & LLM
    DEFAULT_TEMPERATURE: float = 0.0
    
    # Cache Settings
    CACHE_TTL_SECONDS: int = 300

    class Config:
        env_prefix = "DRAFTING_"

# Singleton instance
drafting_config = DraftingConfig()
