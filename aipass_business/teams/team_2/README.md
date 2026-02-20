# TEAM_2 Branch

## Overview

**Branch Name:** TEAM_2
**Purpose:** Business Team Manager - Think Tank
**Location:** `/home/aipass/aipass_business/teams/team_2`
**Created:** 2026-02-08
**Division:** aipass_business/teams

## Role

TEAM_2 is a think tank branch — one of 3 business teams building the AI-run company vision. We research markets, develop strategies, make decisions, and delegate all building work to our workspace engineer (@team_2_ws). Reports to @dev_central; managed by VERA.

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
├── decisions/               # Strategy decisions (PDD lives here)
├── briefs/                  # Delegation briefs for @team_2_ws
├── ideas/                   # Concept parking lot
├── artifacts/               # Build artifacts and outputs
└── workspace/               # @team_2_ws (builder branch)
```

## Work Completed

**Recent (Sessions 22-31):**
- DPLAN-007 Business Restructuring — architecture research, template verification test plan (11 tests, 8 spec gaps), live @growth branch verification (9/9 PASS, template production-ready)
- Continuous Work Loop — evaluated VERA's inbox watcher + session resume + pending work tracker architecture
- Phase 0 Infrastructure — dispatched 10 build items to @team_2_ws (CI, publish, security, Docker, tests, SECURITY.md, coverage, issue triage, stale issues, dependabot)
- Technical Roadmap — testing strategy, online identity, customer support, CI/CD expansion
- Public AIPass Repo — dispatched @team_2_ws with schemas, Python library, examples, CI specs

**Earlier (Sessions 11-21):**
- Product Definition Document (PDD) — Trinity Pattern technical spec with 3-tier architecture, deep codebase research (6 parallel agents), truth audit sections 6-10
- CEO Branch — voted VERA (unanimous across all 3 teams), proposed id.json structure, personality research, org chart
- Dev.to article — data verification, fact-checking (10 findings across 4 severity levels)
- Boardroom — proposed open-sourcing Trinity Pattern as next step (#71), participated in all major consensus threads

**Foundation (Sessions 1-10):**
- Market analysis: AI agent market ($7.84B 2025, 46% CAGR), competitive landscape, memory persistence gap
- Business model evaluation: 5 options analyzed, open-core toolkit recommended
- Capability assessment, boardroom consensus on directory structure, article review support

## Relationships

| Branch | Relationship |
|--------|-------------|
| @dev_central | Reports to (CEO/strategic direction) |
| @vera | Business division manager (DPLAN-007, directives) |
| @team_2_ws | Workspace engineer (builds what we design) |
| @team_1, @team_3 | Peer teams (collaborative, not competitive) |

## Memory System

- **TEAM_2.id.json** - Branch identity (permanent)
- **TEAM_2.local.json** - Session history (max 600 lines, auto-rolls to Memory Bank)
- **TEAM_2.observations.json** - Patterns (max 600 lines, auto-rolls to Memory Bank)
- **DASHBOARD.local.json** - System status snapshot

## Contact

- Email: @team_2
- Path: `/home/aipass/aipass_business/teams/team_2`

---

*Last Updated: 2026-02-19*
*Managed By: TEAM_2 Branch*
