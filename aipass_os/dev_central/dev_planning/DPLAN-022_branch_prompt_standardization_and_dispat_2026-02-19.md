# DPLAN-022: Branch Prompt Standardization & Dispatch Spawn Mode Fixes

Tag: critical

> Two critical infrastructure gaps: 56% of branches have unconfigured system prompts, and the dispatch daemon spawns all branches with `-c` (continue) instead of fresh instances.

## Vision
Every branch in AIPass should have a meaningful system prompt that gives a cold-start Claude instance enough context to operate competently. The dispatch daemon should spawn fresh instances (not continue prior sessions) for dispatched tasks, with heartbeat wakes being the exception (VERA needs `-c` for continuity).

## Current State

### Branch Prompt Audit (2026-02-19)

**32 branches audited.** 14 customized (44%), 18 stubs/defaults (56%).

**Well-customized (models to follow):**
- seed, vera, cortex, api, ai_mail, cli, growth, twitter, admin, trigger, dev_central, backup_system, mcp_servers, feel_good_app

**Unconfigured/Default (NEEDS WORK):**
- drone (FIXED 2026-02-19 by @dev_central), prax, flow, memory_bank, devpulse, commons, research_agent, nft_artifacts, analytics, token_launch, community_manager, social_media, content_creator, market_intelligence, exchange_manager, brand_builder, crypto_brain, partnerships

**Common patterns in good prompts:**
1. "What happens here" - 3-5 sentence summary
2. "Key reminders" - 4-6 critical constraints/patterns
3. Commands reference - key commands with examples
4. Architecture overview - 3-layer structure, key modules
5. Critical operations - mandatory verification steps
6. Working habits - branch-specific principles
7. Domain expertise - what you know vs delegate

### Dispatch Spawn Mode Issue

The dispatch daemon (`daemon.py`) currently uses:
```
claude -c -p "Check inbox for task from {sender}..."
```

The `-c` flag **continues the most recent session** in the branch's CWD. This means:
- Every dispatched task carries forward ALL prior session context
- If the prior session was confused/broken, the new task inherits that state
- Context pollution between unrelated tasks
- Branches can't start clean for isolated work

**VERA is the exception** — she needs `-c` for heartbeat wakes because her management state spans multiple cycles. She needs to remember what teams she dispatched, what's pending, what's stale.

## What Needs Building

### Part 1: Branch Prompt Standardization
- [x] Audit all 32 branches (done 2026-02-19)
- [x] Write drone prompt (done 2026-02-19 — critical routing layer)
- [ ] Define standard template sections (based on good prompt patterns)
- [ ] Write prompts for critical infrastructure: prax, flow, memory_bank, devpulse
- [ ] Write prompts for remaining 13 unconfigured branches
- [ ] Update cortex branch template to include better default prompt

### Part 2: Dispatch Spawn Mode Fix
- [ ] Modify `daemon.py` `spawn_agent()` to use fresh instances (no `-c`) for dispatch wakes
- [ ] Keep `spawn_heartbeat()` using `-c` for VERA's continuity pattern
- [ ] Add configurable spawn mode per branch in safety_config.json (default: fresh)
- [ ] Test fresh spawn with a dispatch task end-to-end
- [ ] Verify VERA heartbeat still works with `-c`

## Design Decisions

| Decision | Options | Leaning | Notes |
|----------|---------|---------|-------|
| Dispatch spawn mode | Fresh (no -c) / Continue (-c) / Configurable per branch | Configurable | Default fresh, VERA overrides to continue |
| Prompt authorship | Branches write their own / DEV_CENTRAL writes all / Self-configuring template | **Self-configuring template** | Default template teaches branches HOW to write their prompt. On first wake, they self-configure. Could solve the whole problem without manual rollout. |
| Standard template | Strict sections / Flexible guidelines | Flexible guidelines | Good prompts vary by role. Define sections, don't enforce order |
| Cortex template update | Include full prompt / Include better starter / Include self-config instructions | **Self-config instructions** | Template should contain: what sections to include, examples from good prompts, instruction to read id.json/README and generate your own. Branch writes its own prompt on first dispatch. |

## Audit Data

### Customized Branches (14) - Prompt Quality Summary

| Branch | Lines | Key Sections |
|--------|-------|-------------|
| seed | 180+ | Standards, checkers, mandatory verification, architecture |
| vera | 120+ | Startup sequence, team routing, dispatch patterns, recovery |
| cortex | 90+ | Branch lifecycle, template system, common pitfalls |
| api | 60+ | OpenRouter, Telegram bridge, model access |
| ai_mail | 50+ | Delivery, inbox, dispatch integration |
| dev_central | 80+ | Orchestration, dispatch, DPLAN workflow, breadcrumbs |
| drone | 80+ | Routing, @ resolution, timeouts, discovery (NEW) |
| cli | 40+ | Rich formatting, display patterns |
| growth | 30+ | Growth strategy, community focus |
| trigger | 30+ | Error registry, alerting |
| backup_system | 30+ | Backup patterns, versioning |
| twitter | 25+ | Twitter API, posting patterns |
| admin | 20+ | Administration, user management |
| mcp_servers | 25+ | MCP protocol, server management |

### Unconfigured Branches (17 remaining after drone fix)

**Critical priority (core infrastructure):**
- prax - Real-time monitoring, Mission Control, event tracking
- flow - Workflow management, FPLAN lifecycle
- memory_bank - AI archive, ChromaDB, auto-rollover
- devpulse - Dev notes, dashboard, DPLAN management

**Medium priority (active branches):**
- commons - The Commons social network
- research_agent - Research tasks

**Lower priority (business/newer branches):**
- nft_artifacts, analytics, token_launch, community_manager, social_media, content_creator, market_intelligence, exchange_manager, brand_builder, crypto_brain, partnerships

## Relationships
- **Related DPLANs:** DPLAN-021 (Telegram hook — also touches daemon spawn patterns)
- **Related FPLANs:** None yet
- **Owner branches:** @dev_central (coordination), @cortex (template updates), @drone (daemon lives in ai_mail but affects all branches)
- **Execution:** Requires Patrick on PC (scheduled Monday 2026-02-23)

## Status
- [x] Planning
- [x] In Progress (drone prompt written, audit complete)
- [ ] Ready for Execution (Monday 2026-02-23)
- [ ] Complete
- [ ] Abandoned

## Schedule
- **Target:** Monday 2026-02-23 (Patrick confirmed availability)
- **Maybe:** Sunday 2026-02-22 (unlikely)
- **Rationale:** Requires Patrick on PC for daemon code changes and testing

## Notes
- Session 115: Full audit completed, drone prompt written as immediate fix
- The `-c -p` spawn issue is the more critical of the two — it affects ALL dispatched work, not just cold starts
- VERA's heartbeat is the only use case that genuinely needs `-c`. All dispatch tasks should start fresh.
- Patrick: "These are critical needs. We will make time for them."
- **Patrick insight (2026-02-19):** The default template should contain instructions on HOW to fill out a local branch prompt. If the template is self-guiding, branches self-configure on first wake — could solve the entire standardization problem without writing 17 prompts manually. Update cortex template to be a teaching document, not a placeholder.

---
*Created: 2026-02-19*
*Updated: 2026-02-19*
