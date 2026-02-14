# AI_MAIL Handlers Documentation

**Date:** 2025-11-30
**Version:** 2.0.0

Handler modules provide independent business logic for AI_Mail operations. Handlers follow strict independence rules: no cross-domain imports, can import Prax services, pure business logic only.

---

## Handler Architecture

**Independence Rules:**
- NO cross-domain imports (handlers cannot import other AI_Mail modules)
- CAN import Prax modules (service providers)
- CAN import AIPASS central services (dashboard)
- Pure business logic only
- Each handler <300 lines

**Handler Tiers:**
- Tier 1: CLI-aware (can use console for display)
- Tier 2: Service-aware (imports Prax/dashboard services)
- Tier 3: Pure functions (raises exceptions, no CLI imports)

---

## 1. Email Handlers (`email/`)

### delivery.py
**Path:** `/home/aipass/aipass_core/ai_mail/apps/handlers/email/delivery.py`
**Purpose:** Delivers emails to branch inboxes, manages inbox.json updates, and dashboard synchronization.
**Version:** 1.1.0

**Key Functions:**
- `get_all_branches() -> List[Dict]` - Reads BRANCH_REGISTRY.json and derives email addresses
- `deliver_email_to_branch(to_branch: str, email_data: Dict) -> Tuple[bool, str]` - Delivers email to target inbox
- `_update_dashboard_section(branch_path, new, opened, total)` - Updates dashboard ai_mail section
- `_get_summary_file_path(branch_path) -> Path` - Gets [BRANCH].ai_mail.json path (deprecated)
- `_update_summary_file(summary_file, message, total, unread)` - Updates summary file (deprecated)

**Notes:**
- Summary files deprecated as of 2025-11-30 (dashboard shows unread count directly)
- Handles email address collisions detection
- Maps email addresses (@branch) to filesystem paths
- Updates central after delivery

---

### inbox_cleanup.py
**Path:** `/home/aipass/aipass_core/ai_mail/apps/handlers/email/inbox_cleanup.py`
**Purpose:** Manages email lifecycle transitions (mark as read, archive to deleted folder). Supports v2 schema (status: new/opened/closed).
**Version:** 2.0.0

**Key Functions:**
- `mark_read_and_archive(branch_path, message_id) -> Tuple[bool, str]` - Mark email read and move to deleted
- `mark_all_read_and_archive(branch_path) -> Tuple[bool, str, int]` - Archive all emails in inbox
- `mark_as_opened(branch_path, message_id) -> Tuple[bool, str, dict]` - Mark email as viewed (v2 schema)
- `mark_as_closed_and_archive(branch_path, message_id) -> Tuple[bool, str]` - Close and archive email (v2 schema)
- `_update_dashboard(branch_path, new, opened, total)` - Updates dashboard with v2 status counts

**V2 Schema:**
- Status transitions: `new` → `opened` → `closed`
- `new` = unviewed email
- `opened` = viewed but not resolved
- `closed` = resolved and archived

---

### reply.py
**Path:** `/home/aipass/aipass_core/ai_mail/apps/handlers/email/reply.py`
**Purpose:** Handles email replies with auto-close functionality for original messages.
**Version:** 1.0.0

**Key Functions:**
- `get_email_by_id(inbox_file, message_id) -> dict | None` - Retrieves email by ID from inbox
- `send_reply(from_branch_path, original_email, reply_message) -> Tuple[bool, str, str]` - Sends reply and auto-closes original

**Workflow:**
1. Finds original email by ID
2. Creates reply with RE: subject
3. Delivers to original sender's inbox
4. Saves to sender's sent folder
5. Auto-closes original email

---

### create.py
**Path:** `/home/aipass/aipass_core/ai_mail/apps/handlers/email/create.py`
**Purpose:** Creates and stores email files in sent folders with timestamped filenames.
**Version:** 1.0.0

**Key Functions:**
- `create_email_file(to_branch, subject, message, user_info) -> Path` - Creates email file in sent folder
- `load_email_file(email_file) -> Dict | None` - Loads email data from file
- `sanitize_subject(subject, max_length=50) -> str` - Sanitizes subject for safe filenames

**Filename Pattern:**
`YYYYMMDD_HHMMSS_sanitized_subject.json`

---

### format.py
**Path:** `/home/aipass/aipass_core/ai_mail/apps/handlers/email/format.py`
**Purpose:** Email display formatting, preview generation, and text utilities.
**Version:** 1.0.0

**Key Functions:**
- `format_email_preview(message, max_length=100) -> str` - Generates preview text with ellipsis
- `format_email_header(email_data) -> str` - Formats email header for display
- `format_email_list_item(index, email_data, show_unread=True) -> str` - Formats inbox list item
- `format_inbox_summary(total_messages, unread_count) -> str` - Formats inbox statistics
- `format_branch_email(branch_name) -> str` - Derives email address from branch name
- `truncate_text(text, max_length, suffix="...") -> str` - Truncates text with suffix

---

### footer.py
**Path:** `/home/aipass/aipass_core/ai_mail/apps/handlers/email/footer.py`
**Purpose:** Email footer generation.

*Documentation pending - handler exists but details not yet documented.*

---

### header.py
**Path:** `/home/aipass/aipass_core/ai_mail/apps/handlers/email/header.py`
**Purpose:** Email header generation.

*Documentation pending - handler exists but details not yet documented.*

---

### inbox_ops.py
**Path:** `/home/aipass/aipass_core/ai_mail/apps/handlers/email/inbox_ops.py`
**Purpose:** Inbox file I/O operations for AI_Mail system.
**Version:** 1.0.0

**Key Functions:**
- `load_inbox(inbox_file) -> Dict` - Loads inbox.json with validation and error handling

**Returns empty dict with messages array if file missing or corrupted.**

---

### purge.py
**Path:** `/home/aipass/aipass_core/ai_mail/apps/handlers/email/purge.py`
**Purpose:** Email purge operations.

*Documentation pending - handler exists but details not yet documented.*

---

## 2. Users Handlers (`users/`)

### user.py
**Path:** `/home/aipass/aipass_core/ai_mail/apps/handlers/users/user.py`
**Purpose:** User information retrieval from branch detection. NO FALLBACKS - fails hard if detection fails.
**Version:** 2.0.0

**Key Functions:**
- `get_current_user() -> Dict` - Gets user info from PWD/CWD (raises RuntimeError if detection fails)
- `get_user_by_email(email) -> Dict | None` - Looks up user by email address
- `get_all_users() -> Dict[str, Dict]` - Returns all users from BRANCH_REGISTRY.json

**Philosophy:**
Fail hard if branch detection fails. Fallbacks hide bugs. Must be called from branch directory with [BRANCH].id.json.

**User Dict Structure:**
```json
{
  "email_address": "@branch",
  "display_name": "BRANCH_NAME",
  "mailbox_path": "/path/to/branch/ai_mail.local",
  "timestamp_format": "%Y-%m-%d %H:%M:%S"
}
```

---

### branch_detection.py
**Path:** `/home/aipass/aipass_core/ai_mail/apps/handlers/users/branch_detection.py`
**Purpose:** Detects which branch is calling AI_MAIL based on PWD/CWD by walking directory tree.
**Version:** 1.0.0

**Key Functions:**
- `detect_branch_from_pwd() -> Dict | None` - Detects branch from current working directory
- `find_branch_root(start_path) -> Path | None` - Walks up tree to find [BRANCH].id.json
- `get_branch_info_from_registry(branch_path) -> Dict | None` - Looks up branch in BRANCH_REGISTRY.json
- `get_branch_display_name(branch_info) -> str` - Generates user-friendly display name
- `get_local_config_path(branch_path, branch_name) -> Path` - Returns path to user_config.json

**Detection Flow:**
1. Get PWD
2. Walk up tree to find [BRANCH].id.json file
3. Look up branch path in BRANCH_REGISTRY.json
4. Return branch info (name, email, path, etc.)

---

### config_generator.py
**Path:** `/home/aipass/aipass_core/ai_mail/apps/handlers/users/config_generator.py`
**Purpose:** Auto-generates user_config.json files and mailbox directories for branches using AI_MAIL.
**Version:** 1.0.0

**Key Functions:**
- `generate_local_config(branch_info) -> Dict` - Generates user_config.json content
- `generate_display_name(branch_info) -> str` - Creates user-friendly display name
- `create_local_config_file(branch_info, force=False) -> Path | None` - Writes config to [branch]_json/
- `create_mailbox_directory(branch_path) -> Path | None` - Creates ai_mail.local/ structure
- `setup_branch_for_aimail(branch_info, force=False) -> bool` - Complete AI_MAIL setup for branch

**Setup Creates:**
- `[branch]_json/user_config.json`
- `ai_mail.local/` mailbox directory
- `ai_mail.local/inbox.json`
- `ai_mail.local/sent.json`

---

## 3. Monitoring Handlers (`monitoring/`)

### memory.py
**Path:** `/home/aipass/aipass_core/ai_mail/apps/handlers/monitoring/memory.py`
**Purpose:** Memory file health monitoring with line counting and status determination.
**Version:** 1.0.0

**Key Functions:**
- `count_file_lines(file_path) -> int` - Counts lines in file (returns 0 on error)
- `get_status_from_count(line_count) -> str` - Determines health status (🟢/🟡/🔴)
- `should_send_email(line_count) -> bool` - Checks if email notification needed (≥600 lines)
- `get_health_info(file_path) -> dict` - Returns complete health analysis
- `format_compression_prompt(file_type, line_count) -> str` - Generates compression agent prompt
- `validate_thresholds(green_max, yellow_min, yellow_max, red_min) -> bool` - Validates threshold config

**Thresholds:**
- Green: 0-400 lines
- Yellow: 401-550 lines
- Red: 551+ lines
- Email trigger: 600+ lines

---

### errors.py
**Path:** `/home/aipass/aipass_core/ai_mail/apps/handlers/monitoring/errors.py`
**Purpose:** Error log parsing, deduplication, and hash generation for error tracking.
**Version:** 1.0.0

**Key Functions:**
- `parse_error_log_line(log_line) -> dict | None` - Parses Prax/Python log format
- `generate_error_hash(module_name, error_message) -> str` - Creates unique error signature (SHA256[:12])
- `get_branch_from_log_path(log_file_path) -> Tuple[str, Path]` - Extracts branch from log path
- `get_ai_mail_file_for_branch(branch_name, branch_root) -> Path | None` - Gets .ai_mail.md path
- `should_exclude_error(module_name) -> bool` - Prevents monitoring of error_monitor's own errors
- `format_error_email(error_hash, error_info, branch_name) -> str` - Formats error notification
- `extract_module_from_log_filename(log_file_path) -> str` - Gets module name from filename
- `validate_error_data_entry(error_info) -> bool` - Validates error tracking structure

**Log Pattern:**
`2025-10-25 15:26:37 - module_name - ERROR - message`

---

### data_ops.py
**Path:** `/home/aipass/aipass_core/ai_mail/apps/handlers/monitoring/data_ops.py`
**Purpose:** Data operations for monitoring subsystem.

*Documentation pending - handler exists but details not yet documented.*

---

## 4. Registry Handlers (`registry/`)

### read.py
**Path:** `/home/aipass/aipass_core/ai_mail/apps/handlers/registry/read.py`
**Purpose:** Reads BRANCH_REGISTRY.json and derives email addresses from branch names.
**Version:** 1.0.0

**Key Functions:**
- `get_all_branches() -> List[Dict]` - Reads registry and returns branch list with emails
- `get_branch_by_email(email) -> Dict | None` - Looks up branch by email address
- `get_branch_email_map() -> Dict[str, str]` - Maps email → branch_name
- `get_branch_path_map() -> Dict[str, str]` - Maps email → path

**Email Derivation Rules:**
- `AIPASS.admin` → `@admin` (part after dot)
- `AIPASS Workshop` → `@aipass` (first word)
- `AIPASS-HELP` → `@help` (second part, avoids collision)
- `BACKUP-SYSTEM` → `@backup` (first part)
- `DRONE` → `@drone` (whole name)

---

### load.py
**Path:** `/home/aipass/aipass_core/ai_mail/apps/handlers/registry/load.py`
**Purpose:** Loads registry files from disk with default structure if missing.
**Version:** 1.0.0

**Key Functions:**
- `load_registry(registry_file) -> Dict` - Loads registry JSON with safe defaults

**Registry Structure:**
```json
{
  "last_updated": "ISO timestamp",
  "active_branches": {},
  "statistics": {
    "total_branches": 0,
    "green_status": 0,
    "yellow_status": 0,
    "red_status": 0
  }
}
```

---

### update.py
**Path:** `/home/aipass/aipass_core/ai_mail/apps/handlers/registry/update.py`
**Purpose:** Updates branch registry with ping data and memory health statistics.
**Version:** 1.0.0

**Key Functions:**
- `ping_registry(branch_name, branch_path, local_status, obs_status) -> bool` - Updates registry
- `get_status_from_count(line_count) -> str` - Determines status code (green/yellow/red)
- `count_file_lines(file_path) -> int` - Counts lines in file
- `update_json_memory_health(file_path, line_count, status_code) -> bool` - Updates JSON metadata
- `get_branch_context() -> Tuple[str, Path]` - Determines branch name and directory from CWD

**Thresholds:**
- Green: 0-400 lines
- Yellow: 401-550 lines
- Red: 551+ lines

---

### validate.py
**Path:** `/home/aipass/aipass_core/ai_mail/apps/handlers/registry/validate.py`
**Purpose:** Validates branch registry data for collisions, duplicates, and structural integrity.
**Version:** 1.0.0

**Key Functions:**
- `check_email_collisions(branches) -> Tuple[bool, List[Dict]]` - Detects email address collisions
- `get_collision_report(collisions) -> str` - Formats collision report
- `validate_branch_data(branch) -> Tuple[bool, str]` - Validates single branch entry
- `validate_all_branches(branches) -> Tuple[bool, List[str]]` - Validates all entries
- `get_duplicate_names(branches) -> List[str]` - Finds duplicate branch names
- `get_duplicate_paths(branches) -> List[str]` - Finds duplicate branch paths

**Validation Checks:**
- Required fields present (name, path, email)
- Email format (@prefix)
- Absolute paths
- No duplicates
- No collisions

---

## 5. Persistence Handlers (`persistence/`)

### json_ops.py
**Path:** `/home/aipass/aipass_core/ai_mail/apps/handlers/persistence/json_ops.py`
**Purpose:** Auto-creating and self-healing JSON system with template support and log rotation.
**Version:** 1.0.0

**Key Functions:**
- `load_template(json_type, module_name) -> Any` - Loads JSON template with placeholder replacement
- `validate_json_structure(data, json_type) -> bool` - Validates JSON structure
- `get_json_path(module_name, json_type) -> Path` - Gets path to module's JSON file
- `ensure_json_exists(module_name, json_type) -> bool` - Creates from template if missing
- `load_json(module_name, json_type) -> Any | None` - Loads JSON with auto-creation
- `save_json(module_name, json_type, data) -> bool` - Saves JSON with validation
- `ensure_module_jsons(module_name) -> bool` - Ensures all 3 JSON files exist (config/data/log)
- `log_operation(operation, data, module_name) -> bool` - Logs operation with auto-rotation
- `increment_counter(module_name, counter_name, amount=1) -> bool` - Increments counter in data JSON
- `update_data_metrics(module_name, **metrics) -> bool` - Updates data metrics

**JSON Types:**
- `config` - Module configuration
- `data` - Persistent data storage
- `log` - Operation log (auto-rotates at max_log_entries)

**Features:**
- Auto-creates missing files from templates
- Self-healing for corrupted files
- Auto-detects calling module for logging
- Log rotation based on config limits

---

## 6. Dispatch Handlers (`dispatch/`)

### status.py
**Path:** `/home/aipass/aipass_core/ai_mail/apps/handlers/dispatch/status.py`
**Purpose:** Dispatch status tracking operations.

*Documentation pending - handler exists but details not yet documented.*

---

## 7. Trigger Handlers (`trigger/`)

### error_handler.py
**Path:** `/home/aipass/aipass_core/ai_mail/apps/handlers/trigger/error_handler.py`
**Purpose:** Error handling for trigger operations.

*Documentation pending - handler exists but details not yet documented.*

---

## 8. Central Writer Handler

### central_writer.py
**Path:** `/home/aipass/aipass_core/ai_mail/apps/handlers/central_writer.py`
**Purpose:** Aggregates branch inbox stats and writes to AI_MAIL.central.json for AIPASS dashboard integration.
**Version:** 1.0.0 (Tier 3: pure functions, raises exceptions)

**Key Functions:**
- `find_all_inbox_files() -> List[Path]` - Scans for all ai_mail.local/inbox.json files
- `extract_branch_name(inbox_path) -> str` - Derives branch name from path
- `read_inbox_stats(inbox_path) -> Tuple[int, int]` - Reads unread and total counts
- `aggregate_branch_stats() -> Dict[str, Dict[str, int]]` - Compiles per-branch statistics
- `calculate_system_totals(branch_stats) -> Dict[str, int]` - Calculates system-wide totals
- `build_central_data(branch_stats) -> Dict[str, Any]` - Builds complete central.json structure
- `write_central_file(data) -> None` - Writes to AI_MAIL.central.json
- `update_central() -> Dict[str, Any]` - **PUBLIC API** - Updates central file with current stats

**Output File:**
`/home/aipass/aipass_os/AI_CENTRAL/AI_MAIL.central.json`

**Central Data Structure:**
```json
{
  "service": "ai_mail",
  "last_updated": "2025-11-30",
  "branch_stats": {
    "SEED": {"unread": 5, "total": 8},
    "DRONE": {"unread": 0, "total": 3}
  },
  "system_totals": {
    "total_unread": 5,
    "total_messages": 11
  }
}
```

**Notes:**
- Excludes backup directories (but not backup_system branch)
- Uses stdlib json via importlib (bypasses local json/ directory)
- Updates dashboard integration automatically
- Called after email delivery/cleanup operations

---

## Handler Usage Patterns

### Basic Usage
```python
# Import handler
from ai_mail.apps.handlers.email.delivery import deliver_email_to_branch

# Use handler function
success, error = deliver_email_to_branch("@flow", email_data)
```

### Error Handling
```python
# Handlers return tuples for error handling
success, message = some_handler_function()
if not success:
    console.print(f"[red]Error:[/red] {message}")
```

### Auto-detection
```python
# User handler auto-detects calling branch
from ai_mail.apps.handlers.users.user import get_current_user

try:
    user_info = get_current_user()  # Raises RuntimeError if detection fails
except RuntimeError as e:
    console.print(f"[red]Detection failed:[/red] {e}")
```

---

## Testing Handlers

All handlers support standalone execution for testing:

```bash
python /home/aipass/aipass_core/ai_mail/apps/handlers/email/delivery.py
```

This displays:
- Handler purpose
- Functions provided
- Handler characteristics
- Usage examples

---

## Handler Dependencies

**Standard Library:**
- json, pathlib, typing, datetime, hashlib, re, uuid, inspect

**Prax Services:**
- `cli.apps.modules.console` - Rich console display

**AIPASS Services:**
- `apps.modules.dashboard.update_section` - Dashboard updates

---

## Design Principles

1. **Independence** - Handlers are self-contained, transportable modules
2. **No Cross-Domain Imports** - Prevents circular dependencies
3. **Fail Hard** - Explicit errors instead of silent fallbacks (user.py philosophy)
4. **Pure Business Logic** - No UI code in handlers
5. **Under 300 Lines** - Keeps handlers focused and maintainable
6. **Template-Based** - Auto-creation from templates for consistency
7. **Self-Healing** - Corrupted files recreated from templates

---

## Future Extensions

Potential handler additions:
- `search/` - Email search and filtering
- `attachments/` - File attachment handling
- `templates/` - Custom email templates
- `rules/` - Email routing rules
- `archive/` - Long-term storage management

---

**Last Updated:** 2025-11-30
**Maintained By:** AI_MAIL Development Team
