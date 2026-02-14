# 3. Architecture

## The Three Memory Files

Every branch maintains three JSON files:

```
BRANCH.id.json           # Identity - who am I
BRANCH.local.json        # History - what have I done
BRANCH.observations.json # Patterns - how we work together
```

---

### Identity (*.id.json)

Rarely changes. Who is this branch?

```json
{
  "name": "FLOW",
  "email": "@flow",
  "role": "Workflow Management",
  "purpose": "Track plans, manage task lifecycle",
  "traits": ["organized", "methodical"]
}
```

---

### Session History (*.local.json)

Updated every session. What happened?

```json
{
  "sessions": [
    {
      "session_number": 12,
      "date": "2026-01-31",
      "activities": [
        "Implemented reply chain validation",
        "Fixed identity mismatch bug"
      ],
      "status": "completed"
    }
  ],
  "active_tasks": {
    "today_focus": "Reply chain validation"
  }
}
```

---

### Observations (*.observations.json)

Meta-patterns. How collaboration works.

```json
{
  "observations": [
    {
      "title": "Memory Updates: Don't Ask, Just Do",
      "insight": "Memories are YOURS - update when notable."
    }
  ]
}
```

---

## Why Three Files?

Separation of concerns:
- **Identity** rarely changes - don't mix with volatile data
- **History** changes often - structured chronologically
- **Observations** are insights - different cadence than activity logs

Each can be compressed, archived, searched independently.
