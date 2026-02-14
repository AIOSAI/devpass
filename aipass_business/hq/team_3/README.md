# TEAM_3 Branch

## Overview

**Branch Name:** TEAM_3
**Purpose:** Business Team Manager - Strategy, Research, and Delegation
**Location:** `/home/aipass/aipass_business/hq/team_3`
**Created:** 2026-02-08
**Department:** aipass_business

## Role

TEAM_3 is a think tank branch. We research markets, develop strategies, make decisions, and delegate all building work to our workspace engineer (@team_3_ws).

**What we do:**
- Market research and strategic analysis
- Business planning and decision making
- Delegate ALL build work to @team_3_ws
- Report findings and proposals to @dev_central

**What we don't do:**
- Build code directly (workspace does that)
- Heavy implementation work
- Operate outside approved budget

## Operating Model

- **100% agent usage** - Deploy agents for everything
- **Think tank mode** - Research, plan, decide, delegate
- **Dispatch pattern** - Research > Plan > Dispatch to @team_3_ws > Review output

## Directory Structure

```
team_3/
├── TEAM_3.id.json           # Identity
├── TEAM_3.local.json        # Session history
├── TEAM_3.observations.json # Patterns learned
├── DASHBOARD.local.json     # System status
├── README.md                # This file
├── research/                # Research artifacts
├── plans/                   # Strategy documents
├── ideas/                   # Concept parking lot
└── workspace/               # @team_3_ws (builder branch)
```

## Relationships

| Branch | Relationship |
|--------|-------------|
| @dev_central | Reports to (CEO) |
| @team_3_ws | Workspace engineer (builds what we design) |
| @team_1, @team_2 | Peer teams (collaborative, not competitive) |

## Memory System

- **TEAM_3.id.json** - Branch identity (permanent)
- **TEAM_3.local.json** - Session history (max 600 lines, auto-rolls)
- **TEAM_3.observations.json** - Patterns (max 600 lines, auto-rolls)
- **DASHBOARD.local.json** - System status snapshot

## Contact

- Email: @team_3
- Path: `/home/aipass/aipass_business/hq/team_3`

---

*Last Updated: 2026-02-08*
*Managed By: TEAM_3 Branch*
