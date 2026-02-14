# API Fallback System - Future Upgrade Plan

**Date:** 2025-10-18
**Status:** Planning phase - NOT implementing yet
**Priority:** Medium (for future enhancement)

## Problem Statement

The API branch is **critical infrastructure** for AIPass:
- Flow system depends on API for plan summarization and memory bank
- Drone system depends on API for compliance checks
- If API fails → multiple systems fail

**Current Risk:**
- Single model dependency
- If model becomes unavailable (privacy settings, provider issues), entire system stops
- 572 consecutive failures before we discovered the issue

## Immediate Fix (COMPLETED ✅)

**What we did:**
- Switched from `deepseek/deepseek-chat-v3.1:free` to `meta-llama/llama-3.3-70b-instruct:free`
- Tested and confirmed working
- Updated both config locations
- System now operational

## Future Enhancement: Cascading Fallback System

### Concept

Instead of failing on first model error, try multiple models in order:

```
Primary Model (Free) → Fallback Model 1 (Free) → Fallback Model 2 (Paid, Cheap) → Return None
```

**User notification:**
- Console warning: "⚠️ Primary model unavailable, switched to [fallback-model]"
- Log entry with details
- NOT silent - Patrick should know when something switches

### Proposed Implementation

**Step 1: Configuration Update**

Add fallback list to `/home/aipass/api/api_json/openrouter_config.json`:

```json
{
  "config": {
    "enabled": true,
    "base_url": "https://openrouter.ai/api/v1",
    "default_model": "meta-llama/llama-3.3-70b-instruct:free",
    "fallback_models": [
      "mistralai/mistral-small-3.2-24b-instruct:free",
      "openai/gpt-4o-mini"
    ],
    "notify_on_fallback": true,
    "timeout_seconds": 30
  }
}
```

**Step 2: Code Enhancement**

Modify `/home/aipass/api/openrouter.py` → `get_response()` function:

```python
def get_response(self, messages, model=None, caller=None, **kwargs):
    """Get AI response with cascading fallback support"""

    # Build model list: requested → default → fallbacks
    models_to_try = []

    if model:
        models_to_try.append(model)

    default = self.config.get("config", {}).get("default_model")
    if default and default not in models_to_try:
        models_to_try.append(default)

    fallbacks = self.config.get("config", {}).get("fallback_models", [])
    for fb in fallbacks:
        if fb not in models_to_try:
            models_to_try.append(fb)

    # Try each model in order
    for i, try_model in enumerate(models_to_try):
        try:
            # Attempt request with this model
            response = self._make_request(messages, try_model, caller, **kwargs)

            if response:
                # Success!
                if i > 0 and self.config.get("config", {}).get("notify_on_fallback", True):
                    # We used a fallback - notify
                    warning = f"⚠️ Primary model unavailable, switched to {try_model}"
                    logger.warning(f"[{MODULE_NAME}] {warning}")
                    log_operation("Fallback used", True, warning)
                    print(warning)  # Console notification

                return response

        except Exception as e:
            # This model failed, try next
            if i < len(models_to_try) - 1:
                logger.info(f"[{MODULE_NAME}] Model {try_model} failed, trying next fallback")
            continue

    # All models failed
    log_operation("Request failed", False, "All models (including fallbacks) failed")
    return None
```

**Step 3: Monitoring Enhancement**

Add fallback tracking to stats:

```json
{
  "fallback_stats": {
    "primary_successes": 1234,
    "fallback_1_used": 5,
    "fallback_2_used": 1,
    "complete_failures": 2
  }
}
```

### Benefits

1. **Resilience:** System stays operational even if primary model fails
2. **Transparency:** Clear warnings when fallbacks are used
3. **Cost Control:** Free models first, cheap paid model as last resort
4. **Monitoring:** Track when/why fallbacks are triggered
5. **Zero-config:** Works automatically for all callers (flow, drone, etc.)

### Recommended Model Cascade

Based on today's testing:

```
1. meta-llama/llama-3.3-70b-instruct:free      (Primary - proven working)
2. mistralai/mistral-small-3.2-24b-instruct:free  (Fallback 1 - also tested working)
3. openai/gpt-4o-mini                          (Fallback 2 - paid but very cheap, proven reliable)
```

**Cost analysis for fallback 2:**
- Your balance: $9.99
- Cost: ~$0.15 per million tokens
- Would only trigger if both free models fail
- Worst case daily cost: < $0.10 if continuously using fallback

### Implementation Phases

**Phase 1: Core Logic** (1-2 hours)
- Add fallback list to config
- Implement cascading try-catch in get_response()
- Add console/log warnings

**Phase 2: Monitoring** (30 min)
- Add fallback usage stats tracking
- Update data file format

**Phase 3: Testing** (30 min)
- Test with all three models
- Simulate failures to test cascade
- Verify flow/drone integration

**Phase 4: Documentation** (15 min)
- Update API.md with fallback system
- Document configuration options

**Total estimated time:** 2-3 hours

### Alternative Approaches Considered

**Option A: Retry with same model**
- ❌ Won't help if model is blocked by privacy settings
- ❌ Wastes time retrying what will always fail

**Option B: Dynamic model selection from available list**
- ❌ Too complex
- ❌ Different models have different capabilities/costs
- ❌ Hard to predict behavior

**Option C: Manual model switching by caller**
- ❌ Puts burden on flow/drone developers
- ❌ Duplicates logic across modules
- ✅ Current approach: centralized in API branch

### Decision Points for Patrick

When ready to implement, decide:

1. **How many fallback levels?** (Recommend 2: one free, one paid)
2. **Notification style?** (Recommend: console warning + log entry)
3. **Cost limit?** (Set max daily spend on paid fallback?)
4. **Health monitoring?** (Alert if primary model fails X times in Y hours?)

### Notes

- This enhancement is **not urgent** - immediate fix is working
- Can implement anytime system load is low
- Good candidate for a PLAN workflow
- Should be tested in dev environment first
- Consider implementing after flow/drone are stable

---

**Summary:** Fallback system would make API branch resilient and self-healing, preventing future outages. Estimated 2-3 hours to implement. Not critical now that immediate fix is working, but valuable future enhancement for system reliability.
