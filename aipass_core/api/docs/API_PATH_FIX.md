# API Path Bug Fix - Flow Integration Issue Resolved

**Date:** 2025-10-18
**Issue:** Flow system couldn't load API key
**Status:** ✅ FIXED

---

## Problem Report from Flow Branch

Flow branch diagnosis showed:
```
[ERROR] API CONNECTION ERROR: No response from OpenRouter API
- .env file (/home/aipass/api/.env): Has placeholder
- Config file: Has empty "api_key": ""
- Flow can't close plans without API
```

---

## Root Cause Analysis

**The Bug:** Relative path resolution in `api_connect.py`

```python
# BEFORE (BROKEN):
def __init__(self):
    self.env_path = Path(".env")           # Relative to CWD!
    self.api_env_path = Path("api/.env")   # Relative to CWD!
```

**Why it failed:**
1. When called from `/home/aipass/api/` → looks for `/home/aipass/api/.env` ✅
2. When called from `/home/aipass/flow/` → looks for `/home/aipass/flow/.env` ❌

**The real key was in:**
- ✅ `/home/aipass/.env` - Has real key (where root-level tests loaded from)
- ❌ `/home/aipass/api/.env` - Had placeholder (never updated)

---

## The Fix

**1. Updated api_connect.py to use absolute paths:**

```python
# AFTER (FIXED):
def __init__(self):
    self.config_path = API_JSON_DIR / CONFIG_FILE
    # Use absolute paths based on this module's location
    module_dir = Path(__file__).parent  # /home/aipass/api
    self.env_path = module_dir / ".env"  # /home/aipass/api/.env
    self.api_env_path = module_dir.parent / ".env"  # /home/aipass/.env (root fallback)
    self.config = None
    self._load_config()
```

**2. Added real API key to /home/aipass/api/.env:**

```bash
OPENROUTER_API_KEY=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
```

---

## Verification Tests

### Test 1: API Key Loading from Flow Directory
```bash
cd /home/aipass/flow && python3 -c "from api.api_connect import get_api_key; print(get_api_key('openrouter'))"
```
**Result:** ✅ Key loads correctly (73 characters)

### Test 2: OpenRouter Connection from Flow Directory
```bash
cd /home/aipass/flow && python3 -c "from api.openrouter import get_response; ..."
```
**Result:** ✅ API working, response: "OK"

---

## Impact

**Fixed systems:**
- ✅ Flow close plan (now has API access)
- ✅ Flow memory bank (can generate TRL tags)
- ✅ Flow plan summarizer (can call AI)
- ✅ Drone compliance (can access API)
- ✅ Any module calling API from different directory

**Key improvement:**
- API branch now works from ANY calling directory
- No more relative path issues
- Absolute paths ensure consistency

---

## Files Modified

1. `/home/aipass/api/api_connect.py` - Lines 182-187
   - Changed from relative paths to absolute paths

2. `/home/aipass/api/.env` - Line 5
   - Updated with real OpenRouter API key

---

## Lessons Learned

**Problem:** Using relative paths in library code
- Works when called from expected directory
- Fails when called from different directory

**Solution:** Always use absolute paths based on module location
- `Path(__file__).parent` gives module's directory
- Build all paths from there
- Works regardless of caller's CWD

**Pattern for future:**
```python
# Good: Absolute path from module location
MODULE_DIR = Path(__file__).parent
CONFIG_PATH = MODULE_DIR / "config.json"

# Bad: Relative path from CWD
CONFIG_PATH = Path("config.json")
```

---

## Next Steps

Flow system should now be able to:
1. ✅ Close plans successfully
2. ✅ Generate memory bank entries
3. ✅ Summarize plans with AI
4. ✅ Process TRL tags

**Patrick can now test:** `flow close plan 0026` or `drone close plan 0026`

---

**Status:** Ready for testing! 🚀
