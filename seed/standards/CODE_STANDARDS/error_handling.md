# Error Handling Standards
**Status:** Active - 3-Tier Logging Architecture
**Date:** 2025-11-21
**Last Major Update:** 2026-01-31 - Added ERROR vs WARNING log level guidelines

## What This Covers

Error handling, logging architecture, exception patterns, and the 3-tier separation of concerns for logging and error management across all AIPass branches.

---

## The 3-Tier Architecture

**Core Principle:** Logging responsibility follows the architectural hierarchy.

```
Entry Point (flow.py, seed.py)
    ↓ (operational logging only)
Module (apps/modules/*.py)
    ↓ (ALL business logging - catches and logs everything)
Handler (apps/handlers/**/*.py)
    ↓ (NO logging - returns results or throws exceptions)
```

**Why This Matters:**
- **Scale:** 17 branches × 50+ handlers = 850+ files to manage
- **Auditability:** Check one directory (modules/) for all business logging
- **Testability:** Automated scans verify compliance
- **Consistency:** Single pattern across entire ecosystem

---

## Tier 1: Entry Points

**Files:** `flow.py`, `seed.py`, `prax.py`, `drone.py`, `ai_mail.py`

**Prax Import:** YES (minimal)

**Logging Scope:** Operational only

**What to Log:**
```python
from prax.apps.modules.logger import system_logger as logger

# ✓ Module discovery results
logger.info(f"Discovered {len(modules)} modules")

# ✓ Command routing
logger.info(f"Routing command '{command}' to module")

# ✓ Help system access
logger.info("Displaying help information")

# ✓ Connection tests
logger.info("Testing Prax connection")
```

**What NOT to Log:**
```python
# ✗ Business errors (module logs these)
logger.error("Failed to create plan")  # NO!

# ✗ Handler exceptions (module logs these)
logger.error("Handler threw exception")  # NO!

# ✗ Validation failures (module logs these)
logger.warning("Invalid input")  # NO!
```

**Characteristics:**
- Operates standalone (help, list modules)
- Same template for all branches (rename only)
- Minimal logging - operational visibility only
- Does NOT catch or log business errors

---

## Tier 2: Modules (THE LOGGING LAYER)

**Location:** `apps/modules/*.py`

**Prax Import:** YES (required)

**Logging Scope:** ALL business logging

**Pattern:**
```python
from prax.apps.modules.logger import system_logger as logger

MODULE_NAME = "create_plan"

def handle_command(command: str, args: List[str]) -> bool:
    """Handle command with full error logging"""

    try:
        # Call handler
        result = create_plan_handler(location, subject)

        if result['success']:
            logger.info(f"[{MODULE_NAME}] Plan created successfully")
            return True
        else:
            logger.error(f"[{MODULE_NAME}] Failed to create plan: {result['error']}")
            return False

    except ValueError as e:
        logger.error(f"[{MODULE_NAME}] Validation error: {e}")
        return False
    except FileNotFoundError as e:
        logger.error(f"[{MODULE_NAME}] File not found: {e}")
        return False
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Unexpected error: {e}")
        return False
```

**What to Log:**
```python
# ✓ All errors
logger.error(f"[{MODULE_NAME}] Operation failed: {error_msg}")

# ✓ All warnings
logger.warning(f"[{MODULE_NAME}] Deprecated feature used")

# ✓ Important info
logger.info(f"[{MODULE_NAME}] Processing 15 items")

# ✓ Workflow boundaries
logger.info(f"[{MODULE_NAME}] Starting workflow")
logger.info(f"[{MODULE_NAME}] Workflow complete")

# ✓ Handler exceptions (caught and logged)
except ValueError as e:
    logger.error(f"[{MODULE_NAME}] Handler validation failed: {e}")
```

---

## Log Level Guidelines: ERROR vs WARNING

**Core Distinction:** ERROR triggers Prax escalation, WARNING does not.

| Level | Use For | Examples |
|-------|---------|----------|
| `logger.error()` | **System failures** - things that shouldn't happen | File I/O errors, crashes, dependency failures, unexpected exceptions, corruption |
| `logger.warning()` | **User input issues** - expected validation failures | "Plan not found", "Field required", "Invalid format", "Already exists" |

**Why This Matters:**
- Prax log_watcher escalates ERROR-level entries to AI_MAIL
- User typos shouldn't trigger system alerts
- ERROR = something is broken; WARNING = user needs to try again

**Pattern:**
```python
# ✓ System failure → ERROR (Prax escalates)
logger.error(f"[{MODULE_NAME}] Failed to write file: {e}")
logger.error(f"[{MODULE_NAME}] Database connection lost")
logger.error(f"[{MODULE_NAME}] Unexpected exception: {e}")

# ✓ User input issue → WARNING (no escalation)
logger.warning(f"[{MODULE_NAME}] Plan {plan_id} not found")
logger.warning(f"[{MODULE_NAME}] Required field 'subject' missing")
logger.warning(f"[{MODULE_NAME}] Invalid format: expected PLAN0001")
```

**CLI Display vs System Logging:**
- CLI can still show "ERROR" text to user (feedback)
- System logs use WARNING level (no Prax escalation)
- These are independent concerns

**Decision:** Approved 2026-01-31 - Rollout to all branches
```

**Logging Pattern Rules:**
1. **Always prefix with MODULE_NAME:** `[{MODULE_NAME}]`
2. **Catch all exceptions from handlers**
3. **Log with context** - what failed, why it matters
4. **Return bool to entry point** - True for success, False for failure

**Responsibilities:**
- Orchestrate handler calls
- Catch exceptions from handlers
- Log everything that goes wrong
- Provide context for debugging
- Return success/failure to entry point

---

## Tier 3: Handlers (THE WORKER LAYER)

**Location:** `apps/handlers/**/*.py`

**Prax Import:** NO (prohibited)

**Logging Scope:** NONE

**Pattern:**
```python
# NO Prax import
# NO logger calls
# Just pure business logic

def create_plan_handler(location: str, subject: str) -> dict:
    """
    Create a plan file

    Returns:
        dict: {'success': bool, 'data': Any, 'error': str}
    """
    # Validate inputs
    if not location:
        return {
            'success': False,
            'data': None,
            'error': 'Location is required'
        }

    # Do the work
    try:
        plan_path = Path(location) / f"PLAN{number:04d}.md"
        plan_path.write_text(content)

        return {
            'success': True,
            'data': {'path': str(plan_path), 'number': number},
            'error': None
        }
    except PermissionError as e:
        # Return error, don't log
        return {
            'success': False,
            'data': None,
            'error': f'Permission denied: {e}'
        }
```

**Return Pattern Options:**

**Option 1: Status Tuple**
```python
def load_config() -> tuple[bool, dict, str]:
    """Returns: (success, data, error_msg)"""
    return True, config_data, None
    # or
    return False, None, "File not found"
```

**Option 2: Status Dict**
```python
def load_config() -> dict:
    """Returns: {'success': bool, 'data': Any, 'error': str}"""
    return {'success': True, 'data': config_data, 'error': None}
    # or
    return {'success': False, 'data': None, 'error': 'File not found'}
```

**Option 3: Raise Exceptions**
```python
def load_config() -> dict:
    """Raises: ValueError, FileNotFoundError"""
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    return config_data
```

**Choose based on context:**
- **Status returns:** When errors are expected (validation, missing files)
- **Exceptions:** When errors are exceptional (corruption, system failures)

**What Handlers MUST NOT Do:**
```python
# ✗ Import Prax
from prax.apps.modules.logger import system_logger as logger  # NO!

# ✗ Call logger
logger.error("Something failed")  # NO!

# ✗ Log anything
print("Debug info")  # NO!
```

**Characteristics:**
- Pure workers - domain-specific tasks
- No side effects (except the core task)
- No logging - return errors instead
- Testable in isolation
- Handler errors caught and logged by modules

---

## Validation Rules

**Automated Compliance Checks:**

```bash
# All modules MUST import Prax
grep -r "from prax.apps.modules.logger import" apps/modules/*.py

# NO handlers can import Prax
grep -r "from prax" apps/handlers/**/*.py  # Should find NOTHING

# NO handlers can call logger
grep -r "logger\." apps/handlers/**/*.py  # Should find NOTHING

# All modules MUST have error logging
grep -r "logger.error" apps/modules/*.py  # Should find ALL modules
```

**Manual Validation:**
1. Run entry point without args - should list modules
2. Run module without args - should list handlers
3. Trigger errors - verify Prax logs capture them
4. Check `logs/` directory for expected output

---

## Migration Checklist

**For Existing Branches:**

1. **Scan handlers for Prax imports**
   ```bash
   grep -r "from prax" apps/handlers/
   ```

2. **Remove Prax from handlers**
   - Delete import statements
   - Remove logger calls
   - Convert logging to return values or exceptions

3. **Add logging to modules**
   - Import Prax in all modules
   - Add try/except around handler calls
   - Log all errors with MODULE_NAME prefix

4. **Test compliance**
   - Run automated scans
   - Test error scenarios
   - Verify logs appear correctly

---

## Common Patterns

### Module Error Handling Template

```python
from prax.apps.modules.logger import system_logger as logger

MODULE_NAME = "module_name"

def handle_command(command: str, args: List[str]) -> bool:
    """Standard error handling pattern"""

    try:
        # Parse arguments
        parsed_args = parse_arguments(args)

        # Call handler
        result = handler_function(**parsed_args)

        # Handle result
        if isinstance(result, dict) and 'success' in result:
            if result['success']:
                logger.info(f"[{MODULE_NAME}] Operation successful")
                return True
            else:
                # WARNING for user input issues, ERROR for system failures
                logger.warning(f"[{MODULE_NAME}] {result['error']}")
                return False
        else:
            logger.info(f"[{MODULE_NAME}] Operation complete")
            return True

    # User input issues → WARNING (no Prax escalation)
    except ValueError as e:
        logger.warning(f"[{MODULE_NAME}] Validation error: {e}")
        return False
    except FileNotFoundError as e:
        # WARNING if user-provided path, ERROR if system config
        logger.warning(f"[{MODULE_NAME}] File not found: {e}")
        return False

    # System failures → ERROR (Prax escalates)
    except PermissionError as e:
        logger.error(f"[{MODULE_NAME}] Permission denied: {e}")
        return False
    except Exception as e:
        logger.error(f"[{MODULE_NAME}] Unexpected error: {e}")
        return False
```

### Handler Return Template

```python
def handler_function(param1: str, param2: int) -> dict:
    """
    Handler that returns status dict

    Args:
        param1: Description
        param2: Description

    Returns:
        dict: {'success': bool, 'data': Any, 'error': str}
    """
    # Validate
    if not param1:
        return {
            'success': False,
            'data': None,
            'error': 'param1 is required'
        }

    # Do work
    try:
        result = do_work(param1, param2)
        return {
            'success': True,
            'data': result,
            'error': None
        }
    except SomeError as e:
        return {
            'success': False,
            'data': None,
            'error': str(e)
        }
```

---

## Why This Pattern Works

**Scalability:**
- Patrick manages 17 branches
- Each branch has 50+ handlers
- Cannot manually audit 850+ files
- Simple rule: modules have Prax, handlers don't

**Auditability:**
- Review `apps/modules/` for all business logging
- No need to search handlers
- One directory contains all error handling

**Testability:**
- Automated scans verify compliance
- Grep checks are fast and reliable
- New branches follow template

**Consistency:**
- All branches use same pattern
- Training new AI instances is simple
- No confusion about "where should I log this?"

---

## Reference

**See Flow for working example:**
- `/home/aipass/aipass_core/flow/apps/modules/`
- `/home/aipass/aipass_core/flow/apps/handlers/`

**See Seed for reference implementation:**
- `/home/aipass/seed/apps/modules/`
- `/home/aipass/seed/apps/handlers/`

**Related Standards:**
- Architecture (3-tier pattern)
- Modules (orchestration responsibility)
- Handlers (pure workers, independence)

---

## Documented Exceptions

### Prax Logging Infrastructure

Prax handlers in `apps/handlers/logging/` use Python's stdlib `logging` instead of `system_logger`. This is **intentional** to avoid circular dependencies.

**Why:** The logging handlers ARE the logging infrastructure. They cannot import from `system_logger` (which depends on them) without creating import cycles.

**Pattern:**
```python
# In prax/apps/handlers/logging/*.py
# Uses stdlib logging to avoid circular dependency with system_logger
import logging
logger = logging.getLogger(__name__)
```

**How it still works:** After `install_logger_override()` runs at Prax initialization, ALL `logging.getLogger()` calls system-wide get routed through Prax's infrastructure anyway.

**Files affected:** `setup.py`, `override.py`, `introspection.py`, `log_watcher.py`, `branch_detector.py`

**Status:** Documented in `/home/aipass/aipass_core/prax/.seed/bypass.json`

---

## Service Logging Standards

**Added:** 2026-02-04
**Applies To:** Services that handle user-facing interactions (bridges, APIs, bots)

### The Gap This Addresses

Services like Telegram bridges, API endpoints, and chat interfaces need more than operational logging. They require:
1. **Content logging** - meaningful records of what happened
2. **Audit trails** - user-facing interactions preserved
3. **Clear location conventions** - where different log types go

### What Services Should Log

**Operational Logs** (Prax-based, existing pattern):
```python
# Status, errors, lifecycle - goes to ~/system_logs/
logger.info(f"[{SERVICE_NAME}] Bridge started on port 8080")
logger.error(f"[{SERVICE_NAME}] Connection lost: {e}")
```

**Content Logs** (Service-specific, new requirement):
```python
# Meaningful interaction records - goes to service's logs/ directory
# Example: Chat bridge logging
content_log = {
    "timestamp": "2026-02-04T10:30:00Z",
    "direction": "inbound",  # or "outbound"
    "user": "user_id",
    "content": "User message text",
    "response": "Bot response text",
    "metadata": {"channel": "telegram", "chat_id": "12345"}
}
```

### Log Location Conventions

| Log Type | Location | Purpose |
|----------|----------|---------|
| **System/operational** | `~/system_logs/` | Prax-captured, cross-branch aggregation |
| **Service content** | `<branch>/logs/` | Service-specific content logs |
| **Audit trails** | `<branch>/logs/audit/` | User-facing interaction records |

**Examples:**
```
~/system_logs/api_telegram.log          # Prax operational log
~/aipass_core/api/logs/chat_history.log # Chat content log
~/aipass_core/api/logs/audit/           # Interaction audit trail
```

### Requirements for User-Facing Services

Services that interact with users (bots, bridges, chat interfaces) MUST:

1. **Log meaningful content, not just status**
   - ✓ "Received message from user X: 'hello'" + "Sent response: 'Hi!'"
   - ✗ "Message received" + "Response sent"

2. **Preserve audit trails for interactions**
   - Chat messages and responses
   - API requests and responses
   - Command invocations and results

3. **Use appropriate log locations**
   - Operational → `~/system_logs/` (via Prax)
   - Content → `<branch>/logs/` (service-managed)

4. **Include sufficient context**
   - Timestamp
   - User/source identifier
   - Direction (inbound/outbound)
   - Content (message, command, response)
   - Relevant metadata

### Content Log Pattern

```python
import json
from datetime import datetime
from pathlib import Path

class ContentLogger:
    def __init__(self, service_name: str, branch_path: Path):
        self.log_dir = branch_path / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / f"{service_name}_content.log"

    def log_interaction(self, direction: str, user: str, content: str,
                       response: str = None, metadata: dict = None):
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "direction": direction,
            "user": user,
            "content": content,
            "response": response,
            "metadata": metadata or {}
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
```

### Why This Matters

**Debugging:** When a user reports "the bot said something wrong", content logs show exactly what happened.

**Auditing:** Compliance, troubleshooting, and understanding system behavior require interaction records.

**Learning:** Patterns in user interactions inform future development.

**Accountability:** Knowing what the system actually said/did, not just that it "worked" or "failed".

---

## Decision Record

**Date:** 2025-11-21
**Decision Maker:** Patrick
**Applies To:** All 17 AIPass branches
**Status:** Approved for rollout
**Pilot Branch:** Flow (completed)
**Next:** Seed update, then remaining 15 branches
