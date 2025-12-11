# Anthropic Prompt Caching Integration Guide

## Overview

Anthropic's Prompt Caching allows you to cache large portions of your prompts on their servers for 5 minutes, providing:
- **90% cost reduction** on cached tokens
- **Faster response times** (reduced latency)
- **Automatic cache management** (no manual invalidation needed)

---

## How It Works

### Cache Markers

Add `cache_control: {"type": "ephemeral"}` to messages you want to cache:

```python
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

# Create LLM with caching enabled
llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",
    temperature=0,
    model_kwargs={
        "extra_headers": {
            "anthropic-beta": "prompt-caching-2024-07-31"
        }
    }
)

messages = [
    # System prompt (CACHED)
    SystemMessage(
        content="You are an expert legal drafter...",
        additional_kwargs={"cache_control": {"type": "ephemeral"}}
    ),

    # Context (CACHED)
    HumanMessage(
        content="Case data: ...\nTemplate: ...\nDocuments: ...",
        additional_kwargs={"cache_control": {"type": "ephemeral"}}
    ),

    # Query (NOT CACHED - changes every time)
    HumanMessage(
        content="Draft the 'Parties' section"
    )
]

response = await llm.ainvoke(messages)
```

---

## Integration into Writer Agent

### Current Implementation (NO caching):

```python
# writer.py - Current
async def write_section(self, state: DraftState):
    section_context = await context_manager.get_section_context(state, section)

    # Simple template filling - NO LLM call
    draft_content = self._generate_draft(section, section_context, citations, state)

    return {"current_draft": draft}
```

### Enhanced Implementation (WITH caching):

```python
# writer.py - Enhanced with LLM + caching
from app.agents.workflows.drafting.llm_utils import (
    create_cached_llm,
    create_cached_messages_with_context
)

class DraftWriter:
    def __init__(self, llm=None):
        # Use cached LLM
        self.llm = llm or create_cached_llm(
            model="claude-3-5-sonnet-20241022",
            provider="anthropic"
        )

    async def write_section(self, state: DraftState):
        # ... get section_context ...

        # Load system prompt (will be cached)
        system_prompt = load_drafting_prompt("writer")

        # Prepare context for caching
        cache_context = {
            "template": section.template_text,
            "case_data": state.get("case_data"),
            "documents": state.get("documents"),
            "previous_sections": section_context["previous_sections"],
            "required_facts": section_context["required_facts"]
        }

        # Create user message (NOT cached - changes per section)
        user_message = f"""Draft the following section:

Section Title: {section.title}
Required Facts: {', '.join(section.required_facts)}
Required Laws: {', '.join(section.required_laws)}

Instructions:
1. Fill all placeholders with facts
2. Use formal Indian legal language
3. Integrate citations naturally
4. Mark missing facts as [MISSING: key]
"""

        # Create messages with caching
        messages = create_cached_messages_with_context(
            system_prompt=system_prompt,
            user_message=user_message,
            context=cache_context,
            cache_system=True,  # Cache the system prompt
            cache_context=True  # Cache the case/template/docs context
        )

        # Invoke LLM (will use cached content if available)
        response = await self.llm.ainvoke(messages)

        # Extract draft content
        draft_content = response.content

        # ... create DraftedSection ...

        return {"current_draft": draft}
```

---

## Cost Analysis

### Example: 4-section Divorce Petition

**Input Breakdown**:
- System prompt: 5,000 tokens (cached)
- Case data: 3,000 tokens (cached)
- Template: 8,000 tokens (cached)
- Documents: 10,000 tokens (cached)
- Query per section: 500 tokens (NOT cached)
- **Total cacheable**: 26,000 tokens
- **Total per request**: 26,500 tokens

### Without Caching:
| Request | Input Tokens | Cost @ $3/1M |
|---------|--------------|--------------|
| Section 1 | 26,500 | $0.0795 |
| Section 2 | 26,500 | $0.0795 |
| Section 3 | 26,500 | $0.0795 |
| Section 4 | 26,500 | $0.0795 |
| **Total** | **106,000** | **$0.318** |

### With Caching (95% hit rate):
| Request | Cached | New | Cost |
|---------|--------|-----|------|
| Section 1 (miss) | 0 | 26,500 | $0.0795 |
| Section 2 (hit) | 26,000 @ $0.30/1M | 500 @ $3/1M | $0.0093 |
| Section 3 (hit) | 26,000 @ $0.30/1M | 500 @ $3/1M | $0.0093 |
| Section 4 (hit) | 26,000 @ $0.30/1M | 500 @ $3/1M | $0.0093 |
| **Total** | - | - | **$0.107** |

**Savings: $0.211 (66% reduction)**

Plus output tokens (not cached):
- 4 sections × 2000 tokens × $15/1M = $0.120
- **Total with output**: $0.227 (vs $0.438 without caching)
- **Final savings: $0.211 (48%)**

---

## Cache Lifetime Strategy

### Cache Duration: 5 minutes

**Optimal Strategy**:
1. Draft all sections in one workflow run (batch processing)
2. Complete workflow within 5 minutes
3. Cache warm for entire document

**Cache Hit Scenarios**:
- ✅ **Section 1 → Section 2**: 100% hit (< 1 minute apart)
- ✅ **Section 2 → Section 3**: 100% hit (< 1 minute apart)
- ✅ **Section 3 → Section 4**: 100% hit (< 1 minute apart)
- ⚠️ **Section 4 → Human Review → Section 5**: May miss if > 5 minutes
- ❌ **Day 1 → Day 2**: Always miss (different day)

**Recommendation**:
- Process one document end-to-end without pauses
- If human review needed, batch multiple sections before review
- For very long documents (> 10 sections), consider checkpoints every 5 sections

---

## What to Cache vs Not Cache

### ✅ Always Cache (Static per case):
1. **System Prompt** (~5000 tokens)
   - Agent role and instructions
   - Output format requirements
   - Writing guidelines

2. **Case Metadata** (~3000 tokens)
   - Case name, number, court
   - Party names
   - Case summary, key facts
   - Prayer/relief sought

3. **Template Content** (~8000 tokens)
   - Full template text
   - Placeholder definitions
   - Section structure

4. **Document Summaries** (~10000 tokens)
   - AI-generated summaries
   - Extracted facts
   - Document metadata

5. **Previously Drafted Sections** (~5000 tokens)
   - For consistency checking
   - For cross-referencing

**Total Cacheable: ~26,000 tokens**

### ❌ Never Cache (Dynamic per section):
1. **Section-Specific Query** (~500 tokens)
   - Current section title
   - Specific instructions
   - Required facts for THIS section

2. **Section-Specific Context** (~1000 tokens)
   - This section's template excerpt
   - This section's dependencies

---

## Monitoring Cache Performance

### Track Cache Hits

Anthropic returns cache hit information in the response:

```python
response = await llm.ainvoke(messages)

# Check usage metadata
usage = response.usage_metadata
print(f"Input tokens: {usage.get('input_tokens', 0)}")
print(f"Cache read tokens: {usage.get('cache_read_input_tokens', 0)}")
print(f"Cache creation tokens: {usage.get('cache_creation_input_tokens', 0)}")

# Calculate hit rate
if usage.get('cache_read_input_tokens', 0) > 0:
    print("✅ Cache HIT")
else:
    print("❌ Cache MISS")
```

### Log Cache Stats

```python
# In writer_node or graph
cache_stats = {
    "section_id": section.id,
    "input_tokens": response.usage_metadata.get('input_tokens', 0),
    "cache_read_tokens": response.usage_metadata.get('cache_read_input_tokens', 0),
    "cache_creation_tokens": response.usage_metadata.get('cache_creation_input_tokens', 0),
    "output_tokens": response.usage_metadata.get('output_tokens', 0),
    "timestamp": datetime.now().isoformat()
}

# Store for analysis
log_cache_stats(cache_stats)
```

---

## Implementation Checklist

- [ ] Update `writer.py` to use `create_cached_llm()`
- [ ] Update `writer.py` to use `create_cached_messages_with_context()`
- [ ] Update `reviewer.py` similarly (if using LLM for validation)
- [ ] Update `planner.py` similarly (if using LLM for planning)
- [ ] Enable Anthropic beta header: `anthropic-beta: prompt-caching-2024-07-31`
- [ ] Structure messages: System (cached) → Context (cached) → Query (not cached)
- [ ] Test with multiple sections in sequence
- [ ] Monitor cache hit rates in production
- [ ] Adjust cache strategy based on document length

---

## Production Configuration

### Environment Variables

```bash
# .env
ANTHROPIC_API_KEY=your_key_here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Enable caching
USE_PROMPT_CACHING=true

# Cache strategy
CACHE_SYSTEM_PROMPT=true
CACHE_CASE_CONTEXT=true
CACHE_TEMPLATE=true
CACHE_DOCUMENTS=true
```

### Configuration Class

```python
# config.py
class DraftingConfig:
    # LLM settings
    MODEL = "claude-3-5-sonnet-20241022"
    TEMPERATURE = 0

    # Caching settings
    USE_PROMPT_CACHING = True
    CACHE_SYSTEM_PROMPT = True
    CACHE_CASE_CONTEXT = True
    CACHE_TEMPLATE = True
    CACHE_DOCUMENTS = True

    # Limits
    MAX_CONTEXT_TOKENS = 30000  # Don't exceed Claude's limits
    MAX_CACHEABLE_TOKENS = 25000  # Leave room for dynamic content
```

---

## Troubleshooting

### Cache Not Working

**Symptom**: All requests show `cache_read_input_tokens: 0`

**Possible Causes**:
1. ❌ Missing beta header: `anthropic-beta: prompt-caching-2024-07-31`
2. ❌ Not using correct model (only Sonnet 3.5+, Opus 3+, Haiku 3+)
3. ❌ Cache expired (> 5 minutes between requests)
4. ❌ Context changed between requests (even small changes invalidate cache)

**Solution**:
```python
# Verify LLM setup
llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",  # ✅ Correct model
    model_kwargs={
        "extra_headers": {
            "anthropic-beta": "prompt-caching-2024-07-31"  # ✅ Required header
        }
    }
)

# Verify message structure
messages = [
    SystemMessage(
        content=prompt,
        additional_kwargs={"cache_control": {"type": "ephemeral"}}  # ✅ Cache marker
    )
]
```

### High Cache Miss Rate

**Symptom**: Cache hit rate < 50%

**Possible Causes**:
1. ❌ Requests too far apart (> 5 minutes)
2. ❌ Context changing between requests (case data updated)
3. ❌ Caching dynamic content (query should NOT be cached)

**Solution**:
- Batch process all sections within 5 minutes
- Don't update case data mid-workflow
- Only cache truly static content

---

## Summary

✅ **Anthropic Prompt Caching**:
- 90% cost reduction on cached tokens
- 5-minute cache lifetime
- Automatic cache management
- Works with Claude 3.5 Sonnet, Opus 3, Haiku 3

✅ **What to Cache**:
- System prompts (~5K tokens)
- Case metadata (~3K tokens)
- Templates (~8K tokens)
- Documents (~10K tokens)
- Previous sections (~5K tokens)

✅ **Expected Savings**:
- 4-section document: 48% cost reduction
- 10-section document: 60% cost reduction
- 100 documents/month: $50-100 saved

✅ **Implementation**:
- Use `llm_utils.py` helper functions
- Structure messages correctly
- Monitor cache hit rates
- Optimize for 5-minute workflow completion
