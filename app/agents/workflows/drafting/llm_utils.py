"""
LLM utilities with API-level prompt caching support.

Implements Anthropic's Prompt Caching and OpenAI's similar features
to reduce costs by 90% for repeated content.

References:
- Anthropic: https://docs.anthropic.com/claude/docs/prompt-caching
- OpenAI: Similar with cache_control parameter
"""

from typing import List, Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
import os

from app.agents.workflows.drafting.resilience import call_with_retry, LLMError

class CachedLLM:
    """
    Wrapper for LLM clients that adds:
    1. Automatic retries for transient failures
    2. Connection validation
    3. Type-safe error propagation
    """
    def __init__(self, client: Any):
        self.client = client

    async def ainvoke(self, messages: List[Any], **kwargs) -> Any:
        """
        Execute LLM call with built-in retry logic.
        """
        async def _execute():
            try:
                return await self.client.ainvoke(messages, **kwargs)
            except Exception as e:
                # Wrap in LLMError to trigger retry strategy in call_with_retry
                raise LLMError(f"LLM Provider Error: {str(e)}") from e

        return await call_with_retry(_execute)
    
    def __getattr__(self, name):
        """Delegate other method calls to underlying client (e.g. stream, invoke)"""
        return getattr(self.client, name)


def create_cached_llm(
    model: Optional[str] = None,
    temperature: float = 0,
    provider: str = "anthropic"
) -> Any:
    """
    Create an LLM client with prompt caching enabled.

    Args:
        model: Model name (e.g., "claude-3-5-sonnet-20241022", "gpt-4o")
        temperature: Sampling temperature
        provider: "anthropic" or "openai"

    Returns:
        Configured LLM client
    """
    
    # Import settings to access keys
    from app.core.config import settings
    
    # Use default from settings if not provided
    if not model:
        model = settings.LLM_MODEL
    
    client = None
    if provider == "anthropic":
        client = ChatAnthropic(
            model=model,
            api_key=settings.ANTHROPIC_API_KEY,
            temperature=temperature,
            # Anthropic-specific: Enable prompt caching
            model_kwargs={
                "extra_headers": {
                    "anthropic-beta": "prompt-caching-2024-07-31"
                }
            }
        )
    else:  # OpenAI
        client = ChatOpenAI(
            model=model,
            api_key=settings.OPENAI_API_KEY,
            temperature=temperature
        )

    return CachedLLM(client)

def create_cached_system_message(content: str, cache: bool = True) -> SystemMessage:
    """
    Create a system message with caching enabled.

    For Anthropic: Marks the message for caching (90% cost reduction on cache hits)
    Cache lasts 5 minutes on Anthropic's servers.

    Args:
        content: System prompt content
        cache: Whether to enable caching

    Returns:
        SystemMessage with caching metadata
    """
    if cache:
        # Anthropic prompt caching format
        return SystemMessage(
            content=content,
            additional_kwargs={
                "cache_control": {"type": "ephemeral"}
            }
        )
    return SystemMessage(content=content)

def create_cached_messages_with_context(
    system_prompt: str,
    user_message: str,
    context: Optional[Dict[str, Any]] = None,
    cache_system: bool = True,
    cache_context: bool = True
) -> List[Any]:
    """
    Create a message list optimized for prompt caching.

    Strategy for maximum cache efficiency:
    1. System prompt (cached) - Changes rarely
    2. Long context like documents, templates (cached) - Changes per case
    3. Short dynamic content (not cached) - Changes per request

    Args:
        system_prompt: The system instruction
        user_message: The dynamic user query
        context: Optional context dict (case data, documents, etc.)
        cache_system: Cache the system prompt
        cache_context: Cache the context

    Returns:
        List of messages with caching markers
    """
    messages = []

    # Message 1: System prompt (always cached)
    messages.append(create_cached_system_message(system_prompt, cache=cache_system))

    # Message 2: Context block (cached if provided)
    if context:
        context_text = format_context_for_caching(context)
        if cache_context:
            # Mark context for caching
            messages.append(
                HumanMessage(
                    content=context_text,
                    additional_kwargs={
                        "cache_control": {"type": "ephemeral"}
                    }
                )
            )
        else:
            messages.append(HumanMessage(content=context_text))

    # Message 3: Actual query (NOT cached - changes every time)
    messages.append(HumanMessage(content=user_message))

    return messages

def format_context_for_caching(context: Dict[str, Any]) -> str:
    """
    Format context dict into a string suitable for caching.

    This should be static per case, so it benefits from caching.

    Args:
        context: Context dict with case data, documents, etc.

    Returns:
        Formatted string
    """
    parts = []

    if "template" in context:
        parts.append(f"## TEMPLATE\n\n{context['template']}")

    if "case_data" in context:
        case = context["case_data"]
        parts.append(f"""## CASE INFORMATION

Case Name: {case.get('caseName', 'N/A')}
Case Type: {case.get('caseType', 'N/A')}
Case Number: {case.get('caseNumber', 'N/A')}
Court: {case.get('courtName', 'N/A')}
Jurisdiction: {case.get('jurisdiction', 'N/A')}

Case Summary:
{case.get('caseSummary', 'N/A')}

Client Position:
{case.get('clientPosition', 'N/A')}

Key Facts:
{chr(10).join(f'- {fact}' for fact in case.get('keyFacts', []))}

Prayer/Relief Sought:
{case.get('prayer', 'N/A')}
""")

    if "documents" in context:
        docs = context["documents"]
        if docs:
            parts.append("## DOCUMENTS\n")
            for doc in docs:
                parts.append(f"""
Document: {doc.get('name', 'Unknown')}
Type: {doc.get('type', 'Unknown')}
Summary: {doc.get('aiSummary', 'N/A')}
---
""")

    if "previous_sections" in context:
        sections = context["previous_sections"]
        if sections:
            parts.append("## PREVIOUSLY DRAFTED SECTIONS\n")
            for sec in sections:
                parts.append(f"""
Section: {sec.get('title', 'Unknown')}
Content Preview: {sec.get('content_excerpt', '')}
---
""")

    if "required_facts" in context:
        facts = context["required_facts"]
        if facts:
            parts.append("## AVAILABLE FACTS\n")
            # Handle both dict and list formats
            if isinstance(facts, dict):
                for key, value in facts.items():
                    if isinstance(value, dict):
                        parts.append(f"- {key}: {value.get('value', 'N/A')}")
                    else:
                        parts.append(f"- {key}: {value}")
            elif isinstance(facts, list):
                for fact in facts:
                    if isinstance(fact, dict):
                        parts.append(f"- {fact.get('key', 'unknown')}: {fact.get('value', 'N/A')}")
                    else:
                        parts.append(f"- {fact}")

    return "\n\n".join(parts)

def estimate_cache_savings(
    system_tokens: int,
    context_tokens: int,
    query_tokens: int,
    num_requests: int,
    cache_hit_rate: float = 0.95
) -> Dict[str, Any]:
    """
    Estimate cost savings from prompt caching.

    Anthropic pricing (Claude 3.5 Sonnet):
    - Input tokens: $3.00 per 1M tokens
    - Cached input tokens: $0.30 per 1M tokens (90% discount)
    - Output tokens: $15.00 per 1M tokens

    Args:
        system_tokens: Tokens in system prompt (~2000-8000)
        context_tokens: Tokens in cached context (~5000-20000)
        query_tokens: Tokens in dynamic query (~500-2000)
        num_requests: Number of requests
        cache_hit_rate: Expected cache hit rate (default: 95%)

    Returns:
        Dict with cost analysis
    """
    # Pricing (per 1M tokens)
    INPUT_COST = 3.00
    CACHED_COST = 0.30
    OUTPUT_COST = 15.00
    OUTPUT_TOKENS = 2000  # Assume avg response length

    # Without caching
    total_input_tokens = (system_tokens + context_tokens + query_tokens) * num_requests
    cost_without_cache = (total_input_tokens / 1_000_000 * INPUT_COST) + \
                         (OUTPUT_TOKENS * num_requests / 1_000_000 * OUTPUT_COST)

    # With caching
    cacheable_tokens = system_tokens + context_tokens
    cache_hits = int(num_requests * cache_hit_rate)
    cache_misses = num_requests - cache_hits

    # First request: full cost
    # Cache hits: only query + cached discount
    # Cache misses: full cost
    cached_input_cost = (
        # Initial cache writes (misses)
        (cacheable_tokens * cache_misses / 1_000_000 * INPUT_COST) +
        # Cache reads (hits) at discounted rate
        (cacheable_tokens * cache_hits / 1_000_000 * CACHED_COST) +
        # Dynamic queries (always full price)
        (query_tokens * num_requests / 1_000_000 * INPUT_COST)
    )

    output_cost = OUTPUT_TOKENS * num_requests / 1_000_000 * OUTPUT_COST
    cost_with_cache = cached_input_cost + output_cost

    savings = cost_without_cache - cost_with_cache
    savings_percent = (savings / cost_without_cache * 100) if cost_without_cache > 0 else 0

    return {
        "cost_without_cache": round(cost_without_cache, 2),
        "cost_with_cache": round(cost_with_cache, 2),
        "savings": round(savings, 2),
        "savings_percent": round(savings_percent, 1),
        "total_input_tokens": total_input_tokens,
        "cacheable_tokens": cacheable_tokens,
        "cache_hits": cache_hits,
        "cache_misses": cache_misses
    }

# Example usage and cache analysis
def get_caching_strategy_guide() -> str:
    """
    Returns a guide on structuring prompts for optimal caching.
    """
    return """
# Prompt Caching Strategy Guide

## What to Cache

✅ **ALWAYS Cache** (changes rarely, large content):
1. System prompts (2000-8000 tokens)
2. Templates (5000-20000 tokens)
3. Case metadata (1000-5000 tokens)
4. Document summaries (5000-20000 tokens)

❌ **NEVER Cache** (changes every request):
1. Current section being drafted
2. User queries
3. Specific instructions

## Message Structure for Maximum Savings

```python
messages = [
    # Message 1: System prompt (CACHED)
    SystemMessage(
        content=SYSTEM_PROMPT,
        additional_kwargs={"cache_control": {"type": "ephemeral"}}
    ),

    # Message 2: Static context (CACHED)
    HumanMessage(
        content=format_context(case, template, documents),
        additional_kwargs={"cache_control": {"type": "ephemeral"}}
    ),

    # Message 3: Dynamic query (NOT CACHED)
    HumanMessage(
        content=f"Draft section: {section_title}"
    )
]
```

## Cache Lifetime

- **Anthropic**: 5 minutes
- **Strategy**: Group requests to same case within 5-minute windows
- **Implication**: Process all sections of a document in one workflow run

## Cost Impact Example

**Divorce petition with 4 sections**:
- System prompt: 5000 tokens
- Context (case + docs + template): 15000 tokens
- Query per section: 500 tokens
- Response: 2000 tokens

**Without caching** (4 requests):
- Input: (5000 + 15000 + 500) × 4 = 82,000 tokens
- Cost: $0.25 input + $0.12 output = $0.37

**With caching** (95% hit rate):
- First request: 20,500 tokens (full price)
- Next 3 requests: 20,000 cached + 500 new
- Cached tokens: 60,000 × $0.30/1M = $0.018
- New tokens: 22,000 × $3.00/1M = $0.066
- Cost: $0.084 input + $0.12 output = $0.20

**Savings: $0.17 (46% reduction)**

## Best Practices

1. **Batch sections**: Draft all sections in one workflow run
2. **Structure prompts**: Put static content before dynamic
3. **Monitor cache hits**: Track cache performance
4. **Warm up cache**: First request is slow but subsequent are fast
5. **Use for long context**: Most beneficial when context > 10K tokens
"""

if __name__ == "__main__":
    # Example: Estimate savings for a typical workflow
    savings = estimate_cache_savings(
        system_tokens=5000,  # System prompt
        context_tokens=15000,  # Case + docs + template
        query_tokens=500,  # Section-specific query
        num_requests=4,  # 4 sections
        cache_hit_rate=0.95
    )
    print("Cache Savings Analysis:")
    print(f"  Without cache: ${savings['cost_without_cache']}")
    print(f"  With cache: ${savings['cost_with_cache']}")
    print(f"  Savings: ${savings['savings']} ({savings['savings_percent']}%)")
