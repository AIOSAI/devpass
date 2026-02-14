# Dashboard & Central API Architecture

**Created:** 2025-11-27
**Updated:** 2025-11-28
**Status:** ✅ COMPLETE - ALL PHASES DONE
**Owner:** AIPASS

---

## Architecture Overview

### The Pattern: Central API Files

Each service maintains its own `.central.json` file in `AI_CENTRAL/`. AIPASS reads from ALL central files to build branch dashboards.

```
┌─────────────────────────────────────────────────────────┐
│                    AI_CENTRAL/                          │
│  (Each service owns ONE file - their "API output")      │
├─────────────────────────────────────────────────────────┤
│  BULLETIN_BOARD_central.json  ← AIPASS owns        ✅   │
│  PLANS.central.json           ← FLOW owns          ✅   │
│  AI_MAIL.central.json         ← AI_MAIL owns       ✅   │
│  MEMORY_BANK.central.json     ← MEMORY_BANK owns   ✅   │
│  DEVPULSE.central.json        ← DEVPULSE owns      ✅   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              AIPASS Dashboard Refresh                   │
│  (Reads all centrals, writes to branch dashboards)      │
├─────────────────────────────────────────────────────────┤
│  1. Read PLANS.central.json → sections.flow        ✅   │
│  2. Read AI_MAIL.central.json → sections.ai_mail   ✅   │
│  3. Read MEMORY_BANK.central.json → sections.memory✅   │
│  4. Read DEVPULSE.central.json → sections.devpulse ✅   │
│  5. Read BULLETIN_BOARD_central.json → bulletins   ✅   │
│  6. Write to all 18 DASHBOARD.local.json files     ✅   │
└─────────────────────────────────────────────────────────┘
```

### Key Principle

**Services NEVER touch dashboards. They maintain their central file. AIPASS owns all dashboards.**

---

## Current Status (2025-11-28)

### Phase 1: Bulletin Board Wiring ✅ COMPLETE
- `propagate_to_branches()` working
- `check_and_propagate()` in Prax logger
- BULLETIN_BOARD_central.json with active toggle
- 18 branches receive bulletins

### Phase 2: Central API Architecture ✅ COMPLETE
- All 5 central files exist with real data
- `handlers/central/reader.py` - reads all centrals
- `handlers/dashboard/refresh.py` - writes 18 dashboards
- `refresh_all_dashboards()` tested: 18/18 success

### Phase 3: Service Integration ✅ COMPLETE

All writers now wired into service operations.

| Service | Writer File | Exists | Wired | Integration Point |
|---------|-------------|--------|-------|-------------------|
| AI_MAIL | `ai_mail/apps/handlers/central_writer.py` | ✅ | ✅ | `email.py` after send/receive |
| MEMORY_BANK | `MEMORY_BANK/apps/handlers/central_writer.py` | ✅ | ✅ | `rollover.py` after rollover |
| DEVPULSE | `devpulse/apps/handlers/central_writer.py` | ✅ | ✅ | `dev_tracking.py` after add |
| FLOW | Uses existing PLANS.central.json | ✅ | ✅ | Already working |

---

## Integration Tasks

### 1. AI_MAIL Integration
**File:** `/home/aipass/aipass_core/ai_mail/apps/modules/email.py`

```python
# Add import at top
from ai_mail.apps.handlers.central_writer import update_central

# After send_email_direct() success (around line 258):
try:
    update_central()
except Exception:
    pass  # Don't break mail ops if central update fails
```

**Also wire into:**
- `delivery.py` after `deliver_email_to_branch()`
- `email.py` after `handle_read()` archive operations

### 2. MEMORY_BANK Integration
**File:** `/home/aipass/MEMORY_BANK/apps/modules/rollover.py`

```python
# Add import at top
from MEMORY_BANK.apps.handlers.central_writer import update_central

# After successful rollover (around line 370):
try:
    update_central()
except Exception:
    pass  # Don't break rollover if central update fails
```

### 3. DEVPULSE Integration
**File:** `/home/aipass/aipass_core/devpulse/apps/modules/dev_tracking.py`

```python
# Add import at top
from devpulse.apps.handlers.central_writer import update_central

# After cmd_add() success (around line 77):
try:
    update_central()
except Exception:
    pass  # Don't break dev add if central update fails
```

---

## File Inventory

### AIPASS (Dashboard Owner)
```
/home/aipass/apps/handlers/
├── central/
│   ├── __init__.py
│   └── reader.py              # read_all_centrals()
├── dashboard/
│   ├── operations.py          # create_fresh_dashboard(), save_dashboard()
│   └── refresh.py             # refresh_all_dashboards()
└── bulletin/
    ├── propagation.py         # propagate_to_branches()
    └── storage.py             # load_bulletins()
```

### AI_MAIL (Mail Stats)
```
/home/aipass/aipass_core/ai_mail/apps/handlers/
└── central_writer.py          # update_central() - EXISTS, NOT WIRED
```

### MEMORY_BANK (Vector Stats)
```
/home/aipass/MEMORY_BANK/apps/handlers/
└── central_writer.py          # update_central() - EXISTS, NOT WIRED
```

### DEVPULSE (Dev Notes)
```
/home/aipass/aipass_core/devpulse/apps/handlers/
└── central_writer.py          # update_central() - EXISTS, NOT WIRED
```

---

## Central File Schemas

### AI_MAIL.central.json
```json
{
  "service": "ai_mail",
  "last_updated": "ISO timestamp",
  "branch_stats": {
    "DRONE": {"unread": 11, "total": 18},
    "FLOW": {"unread": 1, "total": 3}
  },
  "system_totals": {"total_unread": 104, "total_messages": 124}
}
```

### MEMORY_BANK.central.json
```json
{
  "service": "memory_bank",
  "last_updated": "ISO timestamp",
  "stats": {
    "total_vectors": 3354,
    "total_archives": 7,
    "last_rollover": "ISO timestamp"
  }
}
```

### DEVPULSE.central.json
```json
{
  "service": "devpulse",
  "last_updated": "ISO timestamp",
  "branch_summaries": {
    "DRONE": {"notes": 0, "issues": 3, "todos": 0, "ideas": 0}
  }
}
```

---

## Testing Checklist

- [x] All central files exist with valid JSON
- [x] AIPASS can read all centrals without error
- [x] Dashboard refresh populates all sections (18/18)
- [x] AI_MAIL: Send email → central updates automatically
- [x] MEMORY_BANK: Rollover → central updates automatically
- [x] DEVPULSE: Dev add → central updates automatically
- [x] End-to-end: Action → Central → Dashboard shows new data

---

## Trigger Mechanism

Dashboard refresh currently happens via:
1. **Prax Logger** - `_ensure_watcher()` calls `check_and_propagate()` on first log
2. **Manual** - `python3 -c "from apps.handlers.dashboard.refresh import refresh_all_dashboards; refresh_all_dashboards()"`

**Future:** Could add periodic refresh or event-driven triggers.
