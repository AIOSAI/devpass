# DPLAN-010: DevPulse Evolution & dev.local Simplification

> Streamline dev.local.md, add DPLAN tagging + summaries, rethink Memory Bank archival for plans.

## Patrick's Direction (session 112)

- dev.local.md started as quick-capture scratchpad — still valuable for that
- But it's become an everything bucket with mostly-empty sections
- **Slim dev.local to Issues + Todos only.** That's it.
- Ideas should live as DPLANs — DPLANs already cover "ideas, upgrades, proposals, and so forth"
- DPLANs need tags: idea, upgrade, proposal, bug, research, seed — so you can classify what a plan IS
- DPLAN list should generate summaries (like Flow has) — glanceable overview
- Dashboard should show DPLAN counts and status
- **TRL tagging question:** Do we still need TRL (Type-Category-Action) for Memory Bank filenames? Or should plans go direct to Memory Bank vectors, no intermediate markdown in plans/ directory?
- PLANS.central.json and dashboard are probably empty because no open plans exist — need to verify with a test plan or ask Flow
- dev.local has a central system (DEVPULSE.central.json) that aggregates section counts across all branches — section names are hardcoded in multiple places
- The drone `dev add` command should self-heal — but section changes require code updates
- @memory_bank owns the ChromaDB/vector side — devpulse needs to coordinate with them for archival pipeline

## Research Findings (session 112)

**dev.local central system:**
- DEVPULSE.central.json exists at AI_CENTRAL, actively maintained
- Pull-based: central_writer scans all branches' dev.local.md files, counts entries per section
- Triggered on every `drone @devpulse dev add` call — writes entry THEN updates central
- Cortex template creates dev.local.md for new branches with all 6 sections
- **Hardcoded sections in:** cortex template, dev_tracking.py (validation + aliases), central_writer.py (counting), dev status compliance check
- Only 5 branches have dev.local.md so far (all in dev_central subtree) — core branches haven't adopted yet
- Slimming sections requires coordinated code updates, not just file edits

**TRL tagging — KEEP IT:**
- TRL + ChromaDB vectors = hybrid system, complementary not redundant
- Tags: human-browsable filenames, exact filtering ("all UI improvements in SEED")
- Vectors: semantic similarity search via `drone @memory_bank search`
- Both FPLAN and DPLAN processing share the same TRL registry (flow_mbank_registry.json)
- Pipeline: close → AI classifies (OpenRouter) → markdown in MEMORY_BANK/plans/ → rollover embeds to ChromaDB
- 5 processed FPLANs already in MEMORY_BANK/plans/ with TRL names
- Decision: Keep TRL. It serves a different purpose than vectors. Dropping either loses a dimension.

**Memory Bank coordination:**
- @memory_bank owns ChromaDB (all-MiniLM-L6-v2 embeddings, 384-dim, cosine distance)
- Search: `drone @memory_bank search "query"` — semantic, not keyword
- 40% relevance threshold, supports branch/type filtering
- DevPulse's new mbank handler (built 2026-02-18 by close feature) interfaces with this
- Phase 5 needs @memory_bank validation that DPLAN ingestion works correctly

## Current State

**dev.local.md (dev_central):**
- 6 sections: Issues, Upgrades, Testing, Notes, Ideas, Todos
- All empty except Ideas (15+ entries from Jan 31 – Feb 14)
- Ideas range from tiny QoL to massive vision pieces — mixed granularity
- Some ideas already built (Fragmented Memory, Watcher Agent pattern)
- Items get cleared with no trail — just deleted

**DPLAN system:**
- 9 DPLANs exist (002-009), next number: 010
- No tagging/classification — only status checkboxes (Planning, In Progress, etc.)
- List shows bare info: number, topic, date, status icon
- No AI-generated summaries
- No dashboard integration (devpulse section in DASHBOARD.local.json is empty placeholder)
- No registry (filesystem-only tracking — Flow has flow_registry.json)
- Close feature being built right now (dispatched to @devpulse, agent running)

**Flow's infrastructure (reference):**
- flow_registry.json tracks all plans with rich metadata
- PLANS.central.json aggregates across branches → AI_CENTRAL
- plan_summaries.json caches AI-generated summaries
- Dashboard integration: flow_plans section shows active/closed counts
- Self-healing aggregation validates files on disk
- TRL-tagged files in MEMORY_BANK/plans/ directory

**Memory Bank plan archival:**
- Currently: closed plans → AI analyzes → TRL classification → markdown file in MEMORY_BANK/plans/ with naming like `seed-SEED-DEV-IMP-FPLAN-0042-20251202.md`
- Patrick's question: is the TRL-named markdown file useful, or should content go straight to ChromaDB vectors?

## What Needs Building

### Phase 1: dev.local Simplification (coordinated — not just a file edit)
- [ ] Strip dev_central's dev.local.md to Issues + Todos sections only
- [ ] Graduate valid ideas to DPLANs (ones not already captured)
- [ ] Archive stale/built ideas (Fragmented Memory, Watcher Agent, etc.)
- [ ] Update cortex branch template (dev.local.md) — new branches should get slimmed version
- [ ] Update dev_tracking.py — section validation, aliases, accepted sections list
- [ ] Update central_writer.py — counting logic for new section set
- [ ] Update dev status compliance check — reference new sections
- [ ] Update system_prompt.md to reflect new dev.local sections
- [ ] Decide: do existing branches' dev.local.md files get slimmed too, or just new ones?

### Phase 2: DPLAN Tagging
- [ ] Add tag/classification field to DPLAN template
- [ ] Define tag vocabulary: idea, upgrade, proposal, bug, research, seed, infrastructure
- [ ] Update status.py (or new tags.py handler) to extract tags from DPLAN markdown
- [ ] Display tags in plan list output: `DPLAN-010 | DevPulse Evolution | Planning | (idea)`
- [ ] Consider: tag set in template prompt, or free-form?

### Phase 3: DPLAN List with Summaries
- [ ] Add dplan_registry.json (like flow_registry.json) — track plans with metadata
- [ ] AI-generated summaries for each DPLAN (cache in dplan_summaries.json)
- [ ] Enhanced list command: number, topic, tag, status, 1-line summary
- [ ] Filter support: `drone @devpulse plan list --tag idea` or `--status planning`

### Phase 4: Dashboard Integration
- [ ] Push DPLAN data to DASHBOARD.local.json (devpulse section)
- [ ] Show: total plans, by-status breakdown, by-tag breakdown
- [ ] Consider: DEVPULSE.central.json in AI_CENTRAL (parallel to PLANS.central.json)
- [ ] Verify PLANS.central.json + dashboard tracking with a test plan

### Phase 5: Memory Bank Archival Rethink
- [ ] Evaluate TRL tagging: is the naming convention useful for search/retrieval?
- [ ] Option A: Keep TRL (structured filenames help browse MEMORY_BANK/plans/ manually)
- [ ] Option B: Direct to ChromaDB vectors only (no intermediate markdown files)
- [ ] Option C: Both (markdown for human browsing + vectors for AI search)
- [ ] Talk to @memory_bank about current retrieval patterns — does anyone actually browse the plans/ directory?

## Design Decisions

| Decision | Options | Leaning | Notes |
|----------|---------|---------|-------|
| dev.local sections | Issues+Todos / Issues+Todos+Notes / Keep all | Issues+Todos | Patrick confirmed — slim it down |
| DPLAN tag format | Checkbox in template / Metadata line / Filename suffix | Metadata line | `Tag: idea` — parseable, visible, simple |
| Tag vocabulary | Fixed set / Free-form / Both | Fixed set with Other | Consistency matters for filtering |
| DPLAN registry | JSON registry (like Flow) / Filesystem-only | JSON registry | Enables summaries, dashboard push, richer tracking |
| Memory Bank archival | TRL files / ChromaDB only / Both | TBD | Need input from @memory_bank on retrieval patterns |
| Summary generation | On close only / On list (lazy) / Background cron | On close + lazy list | Generate on close, cache; regenerate if stale on list |

## Relationships
- **Related DPLANs:** DPLAN-009 (close feature test)
- **Related FPLANs:** None yet
- **Owner branches:** @devpulse (builds), @dev_central (coordination), @memory_bank (Phase 5 input)
- **Dependencies:** DPLAN close feature (currently being built by @devpulse)

## Status
- [x] Planning
- [ ] In Progress
- [ ] Ready for Execution
- [ ] Complete
- [ ] Abandoned

## Notes
- Session 112 discussion between Patrick and Claude
- The close feature (DPLAN-009 scope) is already dispatched and being built — this DPLAN captures the NEXT evolution
- Phase 1 (dev.local simplification) can happen immediately — it's just a file edit
- Phases 2-4 are a devpulse dispatch
- Phase 5 needs @memory_bank input before deciding
- Patrick: "I don't think we need anything like upgrades. Ideas can get captured into potentially just dev plans."
- Patrick: "Do we need TRL tagging anymore? I'm thinking flow plans all go direct to the memory bank, no store in plans dir."
- PLANS.central.json currently shows 0 active plans, 5 recently closed — probably correct, just no open FPLANs right now

---
*Created: 2026-02-18*
*Updated: 2026-02-18*
