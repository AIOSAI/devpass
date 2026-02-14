# Per-Branch Memory Configuration

**Created:** 2025-11-30
**Status:** Planning
**Owner:** DEV_CENTRAL
**Target:** MEMORY_BANK

---

## Goal

Allow each branch to have custom memory limits (line count for rollover) instead of the hardcoded 600 line default. DEV_CENTRAL specifically wants 800-1000 lines since it's conversation-focused.

---

## Current State

### How Limits Work Now

1. **File-level metadata** - Each `*.local.json` and `*.observations.json` has:
   ```json
   "document_metadata": {
     "limits": {
       "max_lines": 600,
       "max_word_count": 3000,
       "max_token_count": 10000
     }
   }
   ```

2. **Detector reads from metadata** (`detector.py:148`):
   ```python
   return limits.get('max_lines', 600)  # Falls back to 600
   ```

3. **Memory watcher hardcodes 600** (`memory_watcher.py:94`):
   ```python
   ROLLOVER_THRESHOLD = 600  # HARDCODED - ignores metadata
   ```

4. **Config file exists but unused** (`memory_bank.config.json`):
   - Has `limits` section defined
   - Never actually read by rollover/detection code

### Problems

- No per-branch defaults
- Watcher ignores file metadata (uses hardcoded 600)
- Config file is defined but not wired up
- Must manually edit each memory file to change limits

---

## Proposed Solution

### Option A: Branch Registry Approach

Add config to `BRANCH_REGISTRY.json`:

```json
{
  "name": "DEV_CENTRAL",
  "path": "/home/aipass/aipass_os/dev_central",
  "memory_config": {
    "max_lines": 1000,
    "auto_compress_at": 1000,
    "compress_to": 700
  }
}
```

**Pros:** Centralized, already used by detector
**Cons:** Registry is read-only pattern, mixing concerns

### Option B: Memory Bank Config Approach (Recommended)

Add per-branch overrides to `memory_bank.config.json`:

```json
{
  "defaults": {
    "max_lines": 600,
    "compress_to": 400
  },
  "per_branch": {
    "DEV_CENTRAL": {
      "max_lines": 1000,
      "compress_to": 700
    },
    "FLOW": {
      "max_lines": 800
    }
  }
}
```

**Pros:**
- Config file already exists
- Memory Bank owns its own config
- Clear hierarchy (default → branch override → file override)

**Cons:**
- Need to wire it up (currently not read)

### Option C: Branch JSON Directory

Each branch gets a `[branch]_json/memory_config.json`:

```
dev_central/
├── DEV_CENTRAL_json/
│   └── memory_config.json  # Branch-specific config
```

**Pros:** Branch owns its own config
**Cons:** Memory Bank needs to know where to look

---

## Implementation Plan

### Phase 1: Wire Up Config File

**File:** `/home/aipass/MEMORY_BANK/memory_bank_json/memory_bank.config.json`

Add structure:
```json
{
  "rollover": {
    "defaults": {
      "max_lines": 600,
      "compress_to": 400,
      "buffer": 100
    },
    "per_branch": {
      "DEV_CENTRAL": { "max_lines": 1000 }
    }
  },
  "memory_pool": { ... },
  "plans": { ... }
}
```

### Phase 2: Update Detector

**File:** `/home/aipass/MEMORY_BANK/apps/handlers/monitor/detector.py`

Modify `_get_max_lines()`:
```python
def _get_max_lines(file_path: Path, branch_name: str = None) -> int:
    """Get max_lines with priority: file metadata > branch config > default"""

    # 1. Try file-level metadata first
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            file_limit = data.get('document_metadata', {}).get('limits', {}).get('max_lines')
            if file_limit:
                return file_limit
    except Exception:
        pass

    # 2. Try branch-level config
    if branch_name:
        config = _load_config()
        branch_limits = config.get('rollover', {}).get('per_branch', {}).get(branch_name, {})
        if 'max_lines' in branch_limits:
            return branch_limits['max_lines']

    # 3. Fall back to global default
    config = _load_config()
    return config.get('rollover', {}).get('defaults', {}).get('max_lines', 600)
```

### Phase 3: Update Memory Watcher

**File:** `/home/aipass/MEMORY_BANK/apps/handlers/monitor/memory_watcher.py`

Replace line 94:
```python
# OLD: ROLLOVER_THRESHOLD = 600

# NEW: Read from config
def _get_threshold(branch_name: str) -> int:
    config = load_config()
    branch_limits = config.get('rollover', {}).get('per_branch', {}).get(branch_name, {})
    return branch_limits.get('max_lines',
           config.get('rollover', {}).get('defaults', {}).get('max_lines', 600))
```

### Phase 4: Update DEV_CENTRAL Memory Files

After config is wired, update DEV_CENTRAL files:
```json
"limits": {
  "max_lines": 1000,
  "note": "Increased limits - conversation-focused branch"
}
```

---

## Files to Modify

| File | Change | Lines |
|------|--------|-------|
| `memory_bank.config.json` | Add rollover.per_branch section | ~20 |
| `detector.py` | Update `_get_max_lines()` | ~15 |
| `memory_watcher.py` | Replace hardcoded threshold | ~10 |
| DEV_CENTRAL memory files | Update limits in metadata | ~5 each |

---

## Testing

1. Set DEV_CENTRAL to 1000 lines in config
2. Verify detector reads branch config
3. Verify watcher uses config (not hardcoded 600)
4. Test rollover triggers at correct threshold
5. Verify other branches still use default 600

---

## Dependencies

- Memory Bank branch manager or agent to implement
- No breaking changes to existing branches (backwards compatible)

---

## Notes

- Priority order: file metadata > branch config > global default
- This allows emergency per-file overrides while having sensible branch defaults
- Config should be self-documenting with comments/notes fields

---

*Plan created: 2025-11-30*
*Status: Ready for implementation*
