import asyncio
import logging
from typing import TypeVar, Callable, Any, Optional
from functools import wraps

# Setup logger
logger = logging.getLogger(__name__)

T = TypeVar("T")

class WorkflowError(Exception):
    """Base class for all workflow errors."""
    pass

class LLMError(WorkflowError):
    """Errors related to LLM interactions (e.g., API failures)."""
    pass

class RetryableError(WorkflowError):
    """Errors that are transient and can be retried."""
    pass

class ConfigurationError(WorkflowError):
    """Errors related to missing or invalid configuration."""
    pass


async def call_with_retry(
    func: Callable[..., Any],
    max_retries: int = 3,
    base_delay: float = 1.0,
    retryable_exceptions: tuple = (RetryableError, LLMError),
    *args, 
    **kwargs
) -> Any:
    """
    Execute an async function with exponential backoff retry logic.
    
    Args:
        func: The async function to call.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds (multiplied by 2^attempt).
        retryable_exceptions: Tuple of exceptions to trigger a retry.
        *args, **kwargs: Arguments passed to func.
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except retryable_exceptions as e:
            last_exception = e
            
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}. "
                    f"Retrying in {delay}s. Error: {str(e)}"
                )
                await asyncio.sleep(delay)
            else:
                logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}.")
                
        except Exception as e:
            # Non-retryable error
            logger.error(f"Non-retryable error in {func.__name__}: {str(e)}")
            raise e
            
    # Should be raised inside loop, but just in case
    raise last_exception or WorkflowError("Unknown error in retry loop")
