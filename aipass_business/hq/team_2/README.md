# TEAM_2 Branch

## Overview

**Branch Name:** TEAM_2
**Purpose:** Business Team Manager - Think Tank
**Location:** `/home/aipass/aipass_business/hq/team_2`
**Created:** 2026-02-08
**Department:** aipass_business (under HQ)

## Role

TEAM_2 is a think tank branch - one of 3 business teams building the AI-run company vision. We research markets, develop strategies, make decisions, and delegate all building work to our workspace engineer (@team_2_ws).

**What we do:**
- Market research and strategic analysis
- Business planning and decision making
- Delegate ALL build work to @team_2_ws
- Report findings and proposals to @dev_central

**What we don't do:**
- Write code directly (that's @team_2_ws)
- Modify other branches without authorization
- Skip memory updates

## Operating Model

- **100% agent usage** - Deploy agents for everything
- **Think tank mode** - Research, plan, decide, delegate
- **Dispatch pattern** - Research > Plan > Dispatch to @team_2_ws > Review output

## Directory Structure

```
team_2/
├── TEAM_2.id.json           # Identity
├── TEAM_2.local.json        # Session history
├── TEAM_2.observations.json # Patterns learned
├── DASHBOARD.local.json     # System status
├── README.md                # This file
├── research/                # Research artifacts and analysis
├── decisions/               # Strategy decisions
├── ideas/                   # Concept parking lot
├── briefs/                  # Delegation briefs for @team_2_ws
└── workspace/               # @team_2_ws (builder branch)
```

## Work Completed

- Market analysis: AI agent market ($7.84B 2025, 46% CAGR), competitive landscape, memory persistence gap
- Business model evaluation: 5 options analyzed, open-core toolkit recommended
- Capability assessment: tools survey, first-move proposal (publish AIPass case study)
- Boardroom participation: directory structure consensus (decisions/ + briefs/), first-move alignment (Dev.to)
- Article support: fact-checking and data verification for Dev.to article draft

## Relationships

| Branch | Relationship |
|--------|-------------|
| @dev_central | Reports to (CEO/strategic direction) |
| @team_2_ws | Workspace engineer (builds what we design) |
| @team_1, @team_3 | Peer teams (collaborative, not competitive) |

## Memory System

- **TEAM_2.id.json** - Branch identity (permanent)
- **TEAM_2.local.json** - Session history (max 600 lines, auto-rolls to Memory Bank)
- **TEAM_2.observations.json** - Patterns (max 600 lines, auto-rolls to Memory Bank)
- **DASHBOARD.local.json** - System status snapshot

## Contact

- Email: @team_2
- Path: `/home/aipass/aipass_business/hq/team_2`

---

*Last Updated: 2026-02-14*
*Managed By: TEAM_2 Branch*
