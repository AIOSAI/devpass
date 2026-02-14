# AST-Based Business Logic Detection - Test Results
**Date:** 2025-11-25
**Approach:** Python AST parsing to detect module-level data structures

---

## Detection Logic

```python
def detect_business_logic_ast(file_path):
    # 1. Parse file with ast.parse()
    # 2. Walk only top-level tree.body nodes (module level)
    # 3. Find ast.Assign nodes
    # 4. Check if value is ast.List or ast.Dict
    # 5. Count elements - if > 2, flag as violation
    # 6. Return violations with line numbers and details
```

## Test Results

| File | Expected | Status | Violations |
|------|----------|--------|------------|
| sample_violation_list.py | SHOULD FAIL | PASS | 1 |
| sample_violation_dict.py | SHOULD FAIL | PASS | 2 |
| sample_clean.py | SHOULD PASS | PASS | 0 |
| sample_edge_function_scope.py | EDGE CASE | CLEAN | 0 |
| sample_edge_constants.py | EDGE CASE | DETECTED (2 violations) | 2 |
| sample_edge_empty.py | SHOULD PASS | PASS | 0 |

## Detailed Findings

### sample_violation_list.py
- **Expected:** SHOULD FAIL
- **Description:** has hardcoded list
- **Status:** PASS
- **Violations Detected:**
  - Line 10: ignore_patterns = list (8 elements)

### sample_violation_dict.py
- **Expected:** SHOULD FAIL
- **Description:** has hardcoded dicts
- **Status:** PASS
- **Violations Detected:**
  - Line 10: config = dict (4 elements)
  - Line 18: command_handlers = dict (3 elements)

### sample_clean.py
- **Expected:** SHOULD PASS
- **Description:** clean orchestration only
- **Status:** PASS
- **No violations detected**

### sample_edge_function_scope.py
- **Expected:** EDGE CASE
- **Description:** data inside function
- **Status:** CLEAN
- **No violations detected**

### sample_edge_constants.py
- **Expected:** EDGE CASE
- **Description:** ALL_CAPS constants
- **Status:** DETECTED (2 violations)
- **Violations Detected:**
  - Line 13: DEFAULT_PATTERNS = list (3 elements)
  - Line 19: SUPPORTED_FORMATS = dict (3 elements)

### sample_edge_empty.py
- **Expected:** SHOULD PASS
- **Description:** empty structures
- **Status:** PASS
- **No violations detected**

---

## Assessment

### What Works
- **Accurate detection** of module-level list/dict assignments
- **Line numbers** provided for each violation
- **Element counting** to distinguish empty vs populated structures
- **No false positives** on clean orchestration code
- **No false positives** on empty structures
- **Scope-aware** - ignores data inside functions (edge case)

### Limitations
- **ALL_CAPS constants:** Currently flags them as violations
  - Python convention: ALL_CAPS = constant
  - But constants with business logic data are still violations?
  - **Decision needed:** Allow ALL_CAPS or flag them?
- **Threshold arbitrary:** > 2 elements is subjective
- **Cannot detect semantic meaning:** Doesn't know if data is 'business logic'
- **Single file only:** Doesn't check if data is imported from elsewhere

### Edge Case Behavior

**Function-scoped data (sample_edge_function_scope.py):**
- AST correctly ignores data inside functions
- Only checks module-level assignments
- **Verdict:** Working as intended

**ALL_CAPS constants (sample_edge_constants.py):**
- Currently FLAGGED as violations
- Python convention treats ALL_CAPS as constants
- But constants with business logic are still bad architecture
- **Verdict:** Should probably still flag (with warning about constant convention)

**Empty structures (sample_edge_empty.py):**
- Correctly NOT flagged (0 elements)
- Empty list/dict for later population is acceptable
- **Verdict:** Working correctly

### Final Assessment

**Does AST work?** YES
- Successfully detects hardcoded lists and dicts at module level
- Accurately distinguishes module-level from function-level scope
- Provides actionable information (line numbers, variable names)
- No false positives on clean orchestration code

**Recommended approach:**
1. Use AST for detection (proven effective)
2. Add ALL_CAPS detection with INFO-level warning
3. Make threshold configurable (default: > 2 elements)
4. Consider adding docstring checks ("config", "patterns" in variable names)
