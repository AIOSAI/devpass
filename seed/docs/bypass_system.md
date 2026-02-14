# Standards Bypass System

**Branch:** SEED
**Created:** 2025-11-29
**Updated:** 2025-11-29

---

## Overview

The bypass system allows branches to exclude specific code violations from standards validation. This is critical for handling legitimate exceptions where code cannot or should not comply with a particular standard.

**Key principle:** Bypasses are branch-specific, documented, and require explicit justification.

## Key Concepts

- **Branch-specific configuration** - Each branch maintains its own `.seed/bypass.json`
- **Explicit documentation** - Every bypass requires a reason
- **Granular control** - Bypass entire files, specific lines, or pattern matches
- **Auto-creation** - Configuration file is created automatically on first standards check
- **Validation integration** - All 11 standard checkers respect bypass rules

## Configuration Structure

### Location

Each branch stores bypass configuration at:
```
/home/aipass/<branch>/.seed/bypass.json
```

The file is automatically created when `standards_checklist.py` runs against a file in that branch.

### JSON Schema

```json
{
  "metadata": {
    "version": "1.0.0",
    "created": "2025-11-27T16:44:34.325750",
    "description": "Standards bypass configuration for this branch"
  },
  "bypass": [
    {
      "file": "apps/modules/standards_checklist.py",
      "standard": "architecture",
      "lines": [150, 175],
      "pattern": "if __name__ == '__main__'",
      "reason": "Large file justified - orchestrates 12 standards, contains bypass system"
    }
  ],
  "notes": {
    "usage": "Add entries to 'bypass' list to exclude specific violations",
    "example": { ... },
    "fields": { ... }
  }
}
```

## Bypass Fields

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `file` | string | Relative path from branch root (e.g., `apps/modules/logger.py`) |
| `standard` | string | Standard name: `cli`, `imports`, `naming`, `architecture`, `handlers`, `modules`, `documentation`, `json_structure`, `testing`, `error_handling`, `encapsulation` |
| `reason` | string | **Required** - Why this bypass exists. Must be clear and justified. |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `lines` | array | Specific line numbers to bypass (e.g., `[146, 177]`). If omitted, bypasses entire file for this standard. |
| `pattern` | string | Pattern to match (e.g., `"if __name__ == '__main__'"`). Documentation only - not used in matching logic currently. |

## How to Add a Bypass

### Step 1: Run Standards Check

The bypass configuration is auto-created on first run:

```bash
python3 /home/aipass/seed/apps/modules/standards_checklist.py /home/aipass/flow/apps/modules/plan_manager.py
```

This creates `/home/aipass/flow/.seed/bypass.json` if it doesn't exist.

### Step 2: Add Bypass Entry

Open `.seed/bypass.json` and add an entry to the `bypass` array:

```json
{
  "metadata": { ... },
  "bypass": [
    {
      "file": "apps/modules/logger.py",
      "standard": "cli",
      "lines": [146, 177],
      "reason": "Circular dependency - logger cannot import CLI services"
    },
    {
      "file": "apps/handlers/content/cli_content.py",
      "standard": "cli",
      "reason": "Content handler - CLI examples in strings are its PURPOSE (teaching proper usage)"
    }
  ],
  "notes": { ... }
}
```

### Step 3: Verify

Re-run the standards check to confirm the bypass works:

```bash
python3 /home/aipass/seed/apps/modules/standards_checklist.py /home/aipass/flow/apps/modules/plan_manager.py
```

The bypassed violations should no longer appear, and the checker will show:
```
✓ Bypassed: Standard bypassed via .seed/bypass.json
```

## Common Bypass Scenarios

### 1. False Positives in Documentation

**Problem:** Docstrings contain code examples that trigger violations

```json
{
  "file": "apps/handlers/standards/cli_content.py",
  "standard": "cli",
  "reason": "Content handler - CLI examples in strings are its PURPOSE (teaching proper usage)"
}
```

### 2. Circular Dependencies

**Problem:** Module A needs module B, but B cannot import A

```json
{
  "file": "apps/modules/logger.py",
  "standard": "cli",
  "lines": [146, 177],
  "reason": "Circular dependency - logger cannot import CLI services"
}
```

### 3. Legitimate Architectural Exceptions

**Problem:** File orchestrates many systems and is legitimately large

```json
{
  "file": "apps/modules/standards_checklist.py",
  "standard": "architecture",
  "reason": "Large file justified - orchestrates 12 standards, contains bypass system"
}
```

### 4. Direct File Operations Required

**Problem:** Module needs direct file access instead of using handlers

```json
{
  "file": "apps/modules/standards_checklist.py",
  "standard": "modules",
  "reason": "Direct file ops required - reads BRANCH_REGISTRY.json and bypass configs"
}
```

### 5. Not a Three-JSON Use Case

**Problem:** JSON operations don't fit the three-JSON pattern (config/data/log)

```json
{
  "file": "apps/modules/standards_checklist.py",
  "standard": "json_structure",
  "reason": "Direct JSON for bypass system - not three-JSON pattern use case"
}
```

## When to Use Bypasses

### ✅ Appropriate Uses

- **False positives** - Checker detects pattern in strings/comments, not actual code
- **Circular dependencies** - Module A cannot import B due to dependency cycles
- **Architectural necessity** - File legitimately needs to violate standard (e.g., orchestration modules)
- **Implementation vs. usage** - CLI branch implements CLI, doesn't import it
- **Testing/examples** - Test files or content handlers with examples
- **Legacy code** - Temporary bypass while refactoring planned

### ❌ Inappropriate Uses

- **Laziness** - "Don't feel like fixing it"
- **Permanent workarounds** - Code should be fixed, not bypassed indefinitely
- **Hiding technical debt** - Using bypasses to make metrics look better
- **Unclear reasoning** - If you can't explain why, it shouldn't be bypassed
- **Pattern abuse** - Bypassing the same standard across many files suggests architectural problem

## When to Fix Instead

Ask yourself:

1. **Is this actually a problem?** If the checker found a real violation, fix it.
2. **Can I refactor?** Often code can be restructured to comply.
3. **Is this temporary?** Add TODO comments if bypass is meant to be removed later.
4. **Would I accept this in code review?** If not, don't bypass it.

**Golden rule:** Bypasses should be rare. If you're adding many bypasses, you probably have an architectural problem that needs solving.

## How Bypass System Works

### Loading Process

When `standards_checklist.py` runs:

1. **Branch detection** (`get_branch_from_path()`)
   - Reads `/home/aipass/BRANCH_REGISTRY.json`
   - Matches file path to branch using longest-path-first matching
   - Returns branch dict with name, path, etc.

2. **Config initialization** (`ensure_seed_config()`)
   - Checks if `.seed/bypass.json` exists in branch
   - Creates directory and file from template if missing
   - Returns path to bypass configuration

3. **Rule loading** (`load_bypass_rules()`)
   - Reads bypass configuration from `.seed/bypass.json`
   - Extracts `bypass` array
   - Returns list of bypass rule dicts

4. **Rules passed to checkers**
   - Each of 11 standard checkers receives `bypass_rules` parameter
   - Checkers call `is_bypassed()` before reporting violations

### Bypass Checking Logic

The `is_bypassed()` function in `standards_checklist.py`:

```python
def is_bypassed(file_path: str, branch_path: str, standard: str,
                line: Optional[int], bypass_rules: List[Dict]) -> bool:
    """
    Check if a specific violation should be bypassed

    Args:
        file_path: Absolute path to file
        branch_path: Path to branch root
        standard: Standard name (cli, imports, etc.)
        line: Line number of violation (optional)
        bypass_rules: List of bypass rules

    Returns:
        True if this violation should be bypassed
    """
    # Convert to relative path from branch root
    rel_path = str(Path(file_path).relative_to(branch_path))

    for rule in bypass_rules:
        # Must match file and standard
        if rule.get('file') != rel_path:
            continue
        if rule.get('standard') != standard:
            continue

        # Check line-specific bypass
        rule_lines = rule.get('lines', [])
        if rule_lines and line is not None:
            if line in rule_lines:
                return True  # Line-specific bypass matched
        elif not rule_lines:
            return True  # No line restriction - bypass entire file

    return False  # No matching bypass rule
```

### Checker Integration

Each checker implements `is_bypassed()` locally and checks before reporting:

```python
def check_module(module_path: str, bypass_rules: list | None = None) -> Dict:
    # Check if entire standard is bypassed for this file
    if is_bypassed(module_path, 'cli', bypass_rules=bypass_rules):
        return {
            'passed': True,
            'checks': [{'name': 'Bypassed', 'passed': True,
                       'message': 'Standard bypassed via .seed/bypass.json'}],
            'score': 100,
            'standard': 'CLI'
        }

    # ... rest of checking logic
```

## Files Involved

| File | Purpose |
|------|---------|
| `/home/aipass/<branch>/.seed/bypass.json` | Branch-specific bypass configuration |
| `/home/aipass/seed/apps/modules/standards_checklist.py` | Orchestrates bypass loading and checker execution |
| `/home/aipass/seed/apps/handlers/standards/*_check.py` | Individual standard checkers (11 total) |
| `/home/aipass/BRANCH_REGISTRY.json` | Maps file paths to branches for bypass detection |

## Usage Examples

### Check Module with Bypasses

```bash
# The bypass system works automatically
python3 /home/aipass/seed/apps/modules/standards_checklist.py /home/aipass/seed/apps/modules/standards_checklist.py

# Output shows:
# Branch: seed
# Bypass config: /home/aipass/seed/.seed/bypass.json
# Active bypasses: 9
#
# CLI STANDARD:
#   ✓ Bypassed: Standard bypassed via .seed/bypass.json
```

### Via Drone

```bash
drone @seed checklist /home/aipass/flow/apps/modules/plan_manager.py
```

### Inspect Current Bypasses

```bash
cat /home/aipass/seed/.seed/bypass.json | jq '.bypass'
```

## Best Practices

1. **Document thoroughly** - Future you needs to understand why
2. **Be specific** - Use line numbers when possible, not whole-file bypasses
3. **Review regularly** - Periodically check if bypasses are still necessary
4. **Track in version control** - `.seed/bypass.json` should be committed
5. **Justify clearly** - Reason field should explain the "why", not just the "what"
6. **Prefer fixing** - Only bypass when fixing isn't feasible
7. **Consistency** - Similar situations should have similar bypass patterns

## Related

- [Standards Checklist](../apps/modules/standards_checklist.py) - Main orchestration module
- [Standard Checkers](../apps/handlers/standards/) - 11 individual checker implementations
- [Architecture Standards](../../standards/CODE_STANDARDS/architecture.md) - What the checkers validate against
- [README](../README.md) - Seed branch overview

---

*Part of SEED branch documentation - Reference implementation for AIPass standards validation*
