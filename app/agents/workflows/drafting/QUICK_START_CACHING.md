# Quick Start: API-Level Prompt Caching

## ✅ Implementation Complete

API-level prompt caching has been integrated into the Writer and Refiner agents.

---

## What You Need to Know

### 1. How It Works

**Cache Structure** (Optimal for cost savings):
```
Message 1: System Prompt [CACHED - 5K tokens]
Message 2: Context (case/template/docs) [CACHED - 21K tokens]
Message 3: Section-specific query [NOT CACHED - 500 tokens]
```

**Cache Behavior**:
- **First section**: Cache MISS → Full cost → Cache created (lasts 5 minutes)
- **Subsequent sections**: Cache HIT → 90% discount on 26K tokens
- **Result**: 48-66% overall cost reduction

---

## 2. Verify It's Working

### Check 1: Environment Setup

Ensure you have the Anthropic API key:

```bash
# In your .env file
ANTHROPIC_API_KEY=sk-ant-...
```

### Check 2: Run a Test Draft

```python
# Test script
from app.agents.workflows.drafting.graph import create_drafting_graph

# Create graph
graph = create_drafting_graph()

# Run with test data
result = await graph.ainvoke({
    "company_id": "test_company",
    "case_id": "test_case_123",
    "case_type": "divorce",
    # ... other state
})
```

### Check 3: Look for Cache Logs

You should see output like this:

```
[Writer] Drafting Section 1: Parties
  [3/3] Generating draft content with cached LLM...
  ⚡ Cache MISS: 26000 tokens written to cache (available for 5 minutes)
  📊 Tokens: 26500 input, 2000 output

[Writer] Drafting Section 2: Background
  [3/3] Generating draft content with cached LLM...
  ✓ Cache HIT: 26000 tokens read from cache (90% savings)
  📊 Tokens: 26500 input, 1800 output
```

**What to look for**:
- ⚡ **Cache MISS** on first section = Cache created successfully
- ✓ **Cache HIT** on subsequent sections = Cache working!
- No cache logs = Something wrong (see troubleshooting)

---

## 3. Cost Comparison

### Before Caching (4 sections):
```
Section 1: 26500 tokens × $3.00/1M = $0.0795
Section 2: 26500 tokens × $3.00/1M = $0.0795
Section 3: 26500 tokens × $3.00/1M = $0.0795
Section 4: 26500 tokens × $3.00/1M = $0.0795
---
Input cost: $0.318
Output cost: $0.120
Total: $0.438
```

### After Caching (4 sections, 95% hit rate):
```
Section 1 (MISS): 26500 tokens × $3.00/1M = $0.0795
Section 2 (HIT):  26000 × $0.30/1M + 500 × $3.00/1M = $0.0093
Section 3 (HIT):  26000 × $0.30/1M + 500 × $3.00/1M = $0.0093
Section 4 (HIT):  26000 × $0.30/1M + 500 × $3.00/1M = $0.0093
---
Input cost: $0.107
Output cost: $0.120
Total: $0.227
```

**Savings: $0.211 (48%)**

---

## 4. Important Timing Considerations

### Cache Lifetime: 5 Minutes

**✅ GOOD - Cache will work**:
```
10:00:00 - Draft Section 1 (MISS - create cache)
10:00:30 - Draft Section 2 (HIT - 30s later)
10:01:00 - Draft Section 3 (HIT - 1m later)
10:01:30 - Draft Section 4 (HIT - 1m 30s later)
---
All sections drafted within 2 minutes → 3/4 sections use cache
```

**❌ BAD - Cache will expire**:
```
10:00:00 - Draft Section 1 (MISS - create cache)
10:06:00 - Draft Section 2 (MISS - cache expired!)
10:12:00 - Draft Section 3 (MISS - cache expired!)
10:18:00 - Draft Section 4 (MISS - cache expired!)
---
Sections too far apart → No cache benefits
```

**💡 Strategy**: Process all sections in one continuous workflow run

---

## 5. Which Agents Use Caching?

| Agent | Uses LLM? | Has Caching? | Purpose | Quality Impact |
|-------|-----------|--------------|---------|----------------|
| **Writer** | ✅ Yes | ✅ **Integrated** | Generates section content | 🔥 Critical |
| **Refiner** | ✅ Yes | ✅ **Integrated** | Analyzes feedback | 🔥 Critical |
| **Reviewer** | ✅ Yes (Hybrid) | ✅ **Integrated** | 4-level validation (3 rule-based + 1 LLM) | 🔥 Critical |
| **Planner** | ✅ Yes (+ Fallback) | ✅ **Integrated** | Intelligent template parsing | 🔥 Critical |
| **Context Manager** | ❌ No | N/A | Fact/data management | N/A |
| **Citation Agent** | ✅ Yes | ⚠️ Not yet | Tool-based legal research | Medium |

**All 4 critical agents now use LLM with API-level prompt caching!**

### Validation Flow (Reviewer):
```
Level 1: Structural (rule-based) → Check placeholders, format
Level 2: Factual (rule-based) → Verify fact registry
Level 3: Legal (rule-based) → Check citations
Level 4: LLM Deep (cached) → Semantic, reasoning, tone validation
```

### Planning Flow (Planner):
```
Try LLM parsing (cached) → Intelligent section identification
    ↓ (if fails)
Fallback to regex → Regex-based parsing (reliable backup)
```

---

## 6. Troubleshooting

### Problem: No cache logs appearing

**Possible causes**:
1. ❌ Missing Anthropic API key
2. ❌ Wrong model (must be Claude 3.5 Sonnet, Opus 3, or Haiku 3)
3. ❌ Beta header not set

**Solution**:
Check `llm_utils.py` has correct setup:
```python
ChatAnthropic(
    model="claude-3-5-sonnet-20241022",  # ✅ Must be this or compatible
    model_kwargs={
        "extra_headers": {
            "anthropic-beta": "prompt-caching-2024-07-31"  # ✅ Must be present
        }
    }
)
```

### Problem: All sections show Cache MISS

**Possible causes**:
1. ❌ Sections drafted > 5 minutes apart
2. ❌ Context changing between sections
3. ❌ Different LLM instances per section

**Solution**:
- Draft all sections in one workflow run
- Don't modify case data mid-workflow
- Use the same `writer_agent` instance (already configured)

### Problem: Cache HIT but no cost savings

**Possible causes**:
1. ❌ Looking at total cost (includes output tokens, which are never cached)
2. ❌ Using wrong pricing

**Solution**:
- Savings only apply to INPUT tokens
- Check `cache_read_input_tokens` field specifically
- Cached tokens: $0.30/1M (90% discount)
- New tokens: $3.00/1M (full price)

---

## 7. Expected Behavior

### Section 1 (First):
```python
{
  "usage_metadata": {
    "input_tokens": 26500,
    "cache_creation_input_tokens": 26000,  # Cache created
    "cache_read_input_tokens": 0,  # No cache yet
    "output_tokens": 2000
  }
}
```
**Cost**: 26500 × $3/1M + 2000 × $15/1M = $0.1095

### Section 2 (Subsequent):
```python
{
  "usage_metadata": {
    "input_tokens": 26500,
    "cache_creation_input_tokens": 0,  # No new cache
    "cache_read_input_tokens": 26000,  # Reading from cache!
    "output_tokens": 1800
  }
}
```
**Cost**: 26000 × $0.30/1M + 500 × $3/1M + 1800 × $15/1M = $0.0363

**Savings per section**: $0.1095 - $0.0363 = **$0.0732** (67% reduction!)

---

## 8. Files Changed

### Modified Files (All 4 Critical Agents):
1. ✅ `writer.py` - LLM-based content generation with caching
2. ✅ `refiner.py` - LLM-based feedback analysis with caching
3. ✅ `reviewer.py` - Added Level 4 LLM deep validation with caching
4. ✅ `planner.py` - LLM-based intelligent template parsing with caching

### New Files:
5. ✅ `llm_utils.py` - Core caching utilities
6. ✅ `PROMPT_CACHING_INTEGRATION.md` - Detailed integration guide (416 lines)
7. ✅ `API_CACHING_IMPLEMENTATION_SUMMARY.md` - Implementation summary
8. ✅ `QUICK_START_CACHING.md` - This file

### Unchanged Files (by design):
- `context_manager.py` - Data management only (no LLM needed)
- `citation_agent.py` - Already has LLM, but tool-driven (less critical)

---

## 9. Monitoring in Production

### Add to your monitoring dashboard:

```python
# Track cache performance
def track_cache_stats(response):
    if hasattr(response, 'usage_metadata'):
        usage = response.usage_metadata

        metrics = {
            "total_input_tokens": usage.get('input_tokens', 0),
            "cache_read_tokens": usage.get('cache_read_input_tokens', 0),
            "cache_create_tokens": usage.get('cache_creation_input_tokens', 0),
            "output_tokens": usage.get('output_tokens', 0),
            "cache_hit": usage.get('cache_read_input_tokens', 0) > 0,
            "timestamp": datetime.now().isoformat()
        }

        # Log to your monitoring service
        logger.info("LLM_CACHE_STATS", extra=metrics)

        return metrics
```

### Key Metrics to Track:
- **Cache hit rate**: `cache_read_tokens > 0` / total requests
- **Average savings per document**: Compare with/without caching
- **Cache efficiency**: `cache_read_tokens / total_input_tokens`

**Target metrics**:
- Cache hit rate: > 75% (3+ sections per document)
- Average savings: > 40%
- Cache efficiency: > 80%

---

## 10. Next Steps

### To Use in Production:

1. **Set API key**:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

2. **Run workflow**:
```python
from app.agents.workflows.drafting.graph import create_drafting_graph

graph = create_drafting_graph()
result = await graph.ainvoke(initial_state)
```

3. **Monitor logs**: Look for "Cache HIT" messages

4. **Track costs**: Compare before/after in Anthropic console

### To Extend Caching:

If you want to add caching to other agents:

```python
# In any agent file
from app.agents.workflows.drafting.llm_utils import (
    create_cached_llm,
    create_cached_messages_with_context
)

class MyAgent:
    def __init__(self, llm=None):
        self.llm = llm or create_cached_llm(
            model="claude-3-5-sonnet-20241022"
        )

    async def my_method(self, state):
        messages = create_cached_messages_with_context(
            system_prompt=load_prompt("my_agent"),
            user_message="Dynamic query",
            context={"case_data": state.get("case_data")},
            cache_system=True,
            cache_context=True
        )

        response = await self.llm.ainvoke(messages)
        return response
```

---

## 11. Summary

✅ **What's Done** (All 4 Critical Agents Enhanced):
1. **Writer** - LLM-based content generation with caching
2. **Refiner** - LLM-based feedback analysis with caching
3. **Reviewer** - 4-level validation (3 rule-based + 1 LLM with caching)
4. **Planner** - LLM intelligent template parsing with caching (regex fallback)

✅ **Quality Improvements**:
- **Planner**: Intelligent section boundaries, implicit requirements, dependencies
- **Writer**: Natural language generation vs simple template filling
- **Reviewer**: Deep semantic validation (tone, legal reasoning, coherence)
- **Refiner**: Smart feedback classification and actionable instructions

✅ **Expected Cost Savings**:
- 48-66% reduction for multi-section documents
- ~$21/month savings for 100 documents (4 sections avg)
- 90% discount on 26K cached tokens per section
- Applies to ALL 4 LLM-using agents

✅ **How to Verify**:
- Run workflow with 4+ sections
- Check console logs for "Cache HIT" messages in all 4 agents
- Verify Planner says "LLM parsing successful"
- Check Reviewer completes "Level 4: LLM-based deep validation"
- Compare costs in Anthropic dashboard

✅ **Production Ready**:
- No breaking changes
- Backward compatible
- Logging and monitoring included
- Fallback handling for errors (Planner falls back to regex if LLM fails)
- Reviewer continues if LLM validation fails (rule-based validation still works)

---

**Questions or Issues?**

Refer to:
1. `PROMPT_CACHING_INTEGRATION.md` - Detailed technical guide
2. `API_CACHING_IMPLEMENTATION_SUMMARY.md` - Implementation overview
3. `llm_utils.py` - Core utility code and examples

**Test It Now**: Run a workflow and watch for cache logs! 🚀
