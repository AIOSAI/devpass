# Plan: Unified Dashboard Architecture

*Created: 2025-11-24*
*Status: Draft*

---

## Vision

One `DASHBOARD.local.json` per branch that aggregates ALL local notifications and summaries. Each service (Flow, AI_Mail, Memory Bank, Bulletin Board, future systems) manages its own section.

**Current fragmentation:**
- DASHBOARD.local.json (Flow plans only)
- [BRANCH].ai_mail.json (email summaries)
- Various other local files

**Target state:**
- DASHBOARD.local.json contains ALL local summaries
- Each service has its placeholder section
- Services only touch their own section
- One file to check on startup

---

## Architecture

### Central Files (AI_CENTRAL)
```
/home/aipass/aipass_os/AI_CENTRAL/
├── PLANS.central.json          # Flow plan aggregation (exists)
├── BULLETIN_BOARD_central.json # System-wide announcements (created)
├── MARKETPLACE.central.json    # Cross-branch module sharing (future)
└── MEMORY.central.json         # Memory Bank stats (future)
```

### Branch Dashboard (Each Branch)
```json
// DASHBOARD.local.json - Unified format
{
  "branch": "DRONE",
  "last_updated": "2025-11-24T12:00:00Z",

  "sections": {
    "flow": {
      "managed_by": "flow",
      "active_plans": 0,
      "recently_closed": [],
      "last_sync": "timestamp"
    },

    "ai_mail": {
      "managed_by": "ai_mail",
      "unread": 3,
      "total": 15,
      "recent_preview": [...],
      "last_sync": "timestamp"
    },

    "memory_bank": {
      "managed_by": "memory_bank",
      "vectors_stored": 150,
      "archives_count": 12,
      "last_rollover": "timestamp",
      "last_sync": "timestamp"
    },

    "bulletin_board": {
      "managed_by": "aipass",
      "active_bulletins": 1,
      "pending_acknowledgements": ["BULLETIN_0042"],
      "last_sync": "timestamp"
    },

    "marketplace": {
      "managed_by": "marketplace",
      "submitted_modules": 2,
      "available_imports": 15,
      "last_sync": "timestamp"
    }
  },

  "quick_status": {
    "unread_mail": 3,
    "active_plans": 0,
    "pending_bulletins": 1,
    "action_required": true
  }
}
```

### Section Management Pattern

Each service follows the same update pattern:

```python
def update_dashboard_section(branch_path: Path, section_name: str, data: dict) -> bool:
    """Update ONLY your section, preserve all others."""
    dashboard_path = branch_path / "DASHBOARD.local.json"

    # Load existing
    existing = json.loads(dashboard_path.read_text())

    # Update ONLY your section
    existing["sections"][section_name] = data
    existing["sections"][section_name]["last_sync"] = datetime.now().isoformat()

    # Recalculate quick_status
    existing["quick_status"] = calculate_quick_status(existing["sections"])
    existing["last_updated"] = datetime.now().isoformat()

    # Write back
    dashboard_path.write_text(json.dumps(existing, indent=2))
    return True
```

---

## Service Integration

### Flow (Existing - Needs Migration)

**Currently manages:** DASHBOARD.local.json (markdown format for most branches)

**Migration:**
1. Update `update_dashboard_local()` to write to `sections.flow`
2. Keep backward compatibility during transition
3. Eventually remove standalone markdown generation

**Section content:**
```json
"flow": {
  "managed_by": "flow",
  "active_plans": 1,
  "recently_closed": [
    {"id": "PLAN0165", "subject": "...", "closed": "timestamp"}
  ],
  "statistics": {"total_closed": 6}
}
```

### AI_Mail (Needs Migration)

**Currently manages:** [BRANCH].ai_mail.json (separate file)

**Migration:**
1. Update `_update_summary_file()` in delivery.py to write to `sections.ai_mail`
2. Keep [BRANCH].ai_mail.json during transition (for settings)
3. Eventually merge settings into dashboard or branch config

**Section content:**
```json
"ai_mail": {
  "managed_by": "ai_mail",
  "unread": 3,
  "total": 41,
  "recent_preview": [
    {"from": "@seed", "subject": "...", "summary": "15 words..."}
  ]
}
```

### Memory Bank (New Integration)

**Currently:** No dashboard integration

**Add:**
1. Handler to query ChromaDB stats
2. Push to `sections.memory_bank` in each branch's dashboard
3. Show vector counts, archive counts, last rollover

**Section content:**
```json
"memory_bank": {
  "managed_by": "memory_bank",
  "vectors_stored": 150,
  "collections": ["drone_local", "drone_observations"],
  "archives_count": 12,
  "storage_mb": 0.5,
  "last_rollover": "2025-11-23"
}
```

### Bulletin Board (New System)

**Central:** `/home/aipass/aipass_os/AI_CENTRAL/BULLETIN_BOARD_central.json`

**Flow:**
1. AIPASS creates bulletin in central file
2. Propagator pushes to all branch dashboards
3. Branches see `sections.bulletin_board` with pending items
4. Branch acknowledges → updates central file
5. All branches signed → bulletin moves to completed

**Section content:**
```json
"bulletin_board": {
  "managed_by": "aipass",
  "active_bulletins": 1,
  "pending": [
    {
      "id": "BULLETIN_0001",
      "subject": "Add .tracker directory",
      "priority": "low",
      "action_required": "Create .tracker/ in branch root"
    }
  ]
}
```

### Marketplace (Future)

**Concept:** Branches submit their best modules/handlers for cross-branch use

**Section content:**
```json
"marketplace": {
  "managed_by": "marketplace",
  "my_submissions": ["json_handler.py"],
  "available": 15,
  "recently_added": ["prax/cli_formatter.py"]
}
```

---

## Quick Status Block

Top-level summary for instant startup check:

```json
"quick_status": {
  "unread_mail": 3,
  "active_plans": 0,
  "pending_bulletins": 1,
  "memory_warnings": 0,
  "action_required": true,
  "summary": "3 emails, 1 bulletin pending"
}
```

**action_required = true** when:
- Unread mail > 0
- Pending bulletins > 0
- Memory files approaching limit
- Active plans need attention

---

## Migration Strategy

### Phase 1: Add Sections to Existing Dashboard
- Keep current DASHBOARD.local.json format
- Add `sections` object alongside existing content
- Services start writing to their sections
- Backward compatible

### Phase 2: Migrate AI_Mail
- Update delivery.py to write to dashboard
- Keep [BRANCH].ai_mail.json for settings only
- Test with one branch first (seed or drone)

### Phase 3: Add New Services
- Memory Bank integration
- Bulletin Board propagation
- Test end-to-end flow

### Phase 4: Cleanup
- Remove redundant [BRANCH].ai_mail.json files
- Remove markdown dashboard generation
- Update CLAUDE.md startup instructions

---

## Bulletin Board Flow

### Creating a Bulletin (AIPASS)
```bash
# Future command
drone @bulletin create "Subject" "Message" --priority low --type patch
```

Or manually edit `BULLETIN_BOARD_central.json`

### Propagation
1. Central file updated with new bulletin
2. Propagator runs (manual or scheduled)
3. Each branch's DASHBOARD.local.json gets updated
4. `sections.bulletin_board.pending` shows the bulletin

### Branch Acknowledgement
```bash
# Future command (run from branch)
drone @bulletin ack BULLETIN_0001
```

Or autonomous: Branch reads bulletin, performs action, signs automatically

### Completion
- Central file tracks all acknowledgements
- When all target branches sign → bulletin moves to completed
- Dashboard sections auto-update on next sync

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `AI_CENTRAL/BULLETIN_BOARD_central.json` | Created (done) |
| `flow/apps/handlers/dashboard/update_local.py` | Modify for sections |
| `ai_mail/apps/handlers/email/delivery.py` | Add dashboard section update |
| `memory_bank/apps/handlers/dashboard/` | Create new handler |
| New: `bulletin_board/` module | Create for propagation |
| `DASHBOARD.local.json` template | Update in cortex templates |

---

## Multi-AI Compatibility

**Claude Code:** Has system prompt with drone commands
**Other AIs (GPT, Gemini, Local):**
- Read DASHBOARD.local.json directly
- Use drone commands via API/subprocess
- Same data, different interface

Dashboard is **AI-agnostic** - just JSON files that any AI can read.

---

## Open Questions

1. **Who manages propagation?** AIPASS directly or dedicated bulletin module?
2. **Sync frequency?** On every dashboard read, or scheduled refresh?
3. **Settings location?** Keep in [BRANCH].ai_mail.json or move to config?
4. **Quick status calculation?** Each service updates, or central recalc?

---

## Success Criteria

- Branch startup: Read ONE file, know everything
- Services isolated: Each manages only its section
- Central aggregation: System-wide view at AI_CENTRAL
- Autonomous ready: Branches can act on bulletins without human intervention
- Token efficient: ~150 lines max for full dashboard

---

*This unifies the fragmented notification landscape into a single, extensible dashboard system.*
