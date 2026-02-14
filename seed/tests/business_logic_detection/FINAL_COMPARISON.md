# Business Logic Detection - Final Comparison

**Date:** 2025-11-25
**Tested by:** Seed Branch

---

## Test Results Summary

| Approach | Test Pass Rate | Speed | Complexity | Recommendation |
|----------|---------------|-------|------------|----------------|
| Line Scan | 100% (6/6) | Fastest | Simple | Good for quick checks |
| AST | 100% (6/6) | Medium | Medium | Good for accuracy |
| **Hybrid** | 100% (6/6) | Fast on clean files | Medium | **RECOMMENDED** |

---

## Approach Comparison

### 1. Line Scanning (test_line_scan.py)
**How it works:** Regex pattern matching on raw text
- Fast: O(n) where n = lines
- No parsing overhead
- Can miss context (function scope vs module level)

**Strengths:**
- Very fast
- Simple code (~150 lines)
- No dependencies beyond regex

**Weaknesses:**
- Can't distinguish function-level from module-level
- May have false positives without scope checking

### 2. AST (test_ast_detect.py)
**How it works:** Python ast.parse() to analyze syntax tree
- Accurate: Knows exact scope and context
- Gets element counts, types, line numbers
- Slower: Must parse entire file

**Strengths:**
- 100% accurate scope detection
- Rich metadata (counts, types)
- Handles all Python syntax correctly

**Weaknesses:**
- Always parses (slower on clean files)
- More memory usage
- More complex code

### 3. Hybrid (test_hybrid.py) - RECOMMENDED
**How it works:** Line scan first, AST only if candidates found
- Fast on clean files (no parsing)
- Accurate on violations (AST verification)

**Strengths:**
- Best of both worlds
- Fast when no violations
- Accurate when violations exist
- Good edge case handling

**Weaknesses:**
- Two-phase complexity
- Potential false negatives if line scan misses pattern

---

## Key Finding: The Real standards_audit.py Case

**Expected:** The `ignore_patterns` list in standards_audit.py should be flagged

**Actual:** NOT flagged by any approach

**Why:** The `ignore_patterns` is defined INSIDE the `audit_branch()` function (line 243), not at module level. All three detectors correctly identify this as function-scoped data.

```python
# Line 227 - Function definition
def audit_branch(branch: Dict[str, str]) -> Dict:
    ...
    # Line 243 - Inside function, NOT module level
    ignore_patterns = [
        '__pycache__',
        'archive',
        ...
    ]
```

---

## Design Decision Required

The user's original concern was about business logic in modules. But there are TWO interpretations:

### Option A: Module-Level Only (Current Behavior)
- Only flag data structures at the module level (top of file)
- Function-local data is acceptable (temporary/processing data)
- **Rationale:** Function data is scoped, doesn't persist, different semantically

### Option B: All Business Data (Stricter)
- Flag ANY hardcoded data structure, regardless of scope
- Even function-local data should be in handlers
- **Rationale:** Business logic is business logic, location doesn't matter

**Current implementation:** Option A (module-level only)

**To switch to Option B:** Remove the `_is_module_level()` check in hybrid detector

---

## Files Created

```
/home/aipass/seed/tests/business_logic_detection/
├── test_line_scan.py      # Line scanning approach
├── test_ast_detect.py     # AST-based approach
├── test_hybrid.py         # Hybrid approach (RECOMMENDED)
├── results_line_scan.md   # Line scan results
├── results_ast.md         # AST results
├── results_hybrid.md      # Hybrid results
├── SUMMARY.md             # Hybrid summary
├── FINAL_COMPARISON.md    # This file
└── sample_*.py            # Test modules (6 files)
```

---

## Next Steps

1. **Decide:** Module-level only vs all scopes?
2. **Integrate:** Add chosen approach to modules_check.py
3. **Test:** Run against real codebase
4. **Iterate:** Adjust filters based on false positives/negatives

---

## Recommendation

Use **Hybrid approach** with **module-level only** detection:
- Catches the most egregious cases (module-level business data)
- Doesn't over-flag function-local processing data
- Fast and accurate
- Easy to adjust if needed

If stricter detection is needed later, the hybrid detector can be modified to include function-scoped data as well.
