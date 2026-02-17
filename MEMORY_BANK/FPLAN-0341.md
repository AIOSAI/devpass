# FPLAN-0341 - Fragment Extraction v2 - LLM-Based Memory Extraction (MASTER PLAN)

**Created**: 2026-02-15
**Branch**: /home/aipass/MEMORY_BANK
**Status**: Active
**Type**: Master Plan (Multi-Phase)

---

## What Are Flow Plans?

Flow Plans (FPLANs) are for **BUILDING** - autonomous construction of systems, features, modules. They're the structured way to execute work without constant human oversight.

**This is NOT for:**
- Research or exploration (use agents directly)
- Quick fixes (just do it)
- Discussion or planning (that happens before creating the FPLAN)

**This IS for:**
- Building new branches/modules
- Implementing features
- Multi-phase construction projects
- Autonomous execution

---

## Master Plan vs Default Plan

| | Master Plan | Default Plan |
|---|-------------|--------------|
| **Use when** | 3+ phases, complex build | Single focused task |
| **Structure** | Roadmap + sub-plans | Self-contained |
| **Phases** | Multiple, sequential | One |
| **Sub-plans** | Yes, one per phase | No |
| **Typical use** | Build entire branch | One phase of master |

**Pattern:**
```
Master Plan (roadmap)
├── Sub-plan Phase 1 (default template)
├── Sub-plan Phase 2 (default template)
├── Sub-plan Phase 3 (default template)
└── Sub-plan Phase 4 (default template)
```

**How to start:**
1. DEV_CENTRAL provides planning doc or instructions
2. Branch manager reads and understands scope
3. Branch manager creates master plan: `drone @flow create . "Build X" master`
4. Branch manager fills in phases, then executes autonomously

---

## Critical: Branch Manager Role

**You are the ORCHESTRATOR, not the builder.**

Your 200k context is precious. Burning it on file reads and code writing risks compaction during autonomous work. Agents have clean context - use them for ALL building.

| You Do (Orchestrator) | Agents Do (Builders) |
|-----------------------|----------------------|
| Create plans & sub-plans | Write code |
| Define phases | Run tests |
| Give agent instructions | Read/modify files |
| Review agent output | Research/exploration |
| Course correct | Heavy lifting |
| Update memories | Single-task execution |
| Send status emails | Build deliverables |
| Track phase progress | Quality checks on code |

**Master Plan Pattern:** Define all phases → Create sub-plan for Phase 1 → Deploy agent → Review → Close sub-plan → Email update → Next phase

---

## Seek Branch Expertise

Don't figure everything out alone. Other branches are domain experts - ask them first.

**Before building anything that touches another branch's domain:**
```bash
ai_mail send @branch "Question: [topic]" "I'm working on X and need guidance on Y. What's the best approach?"
```

**Common examples:**
- Building something with email? Ask @ai_mail how delivery works
- Need routing or @ resolution? Ask @drone
- Unsure about standards? Ask @seed for reference code
- Need persistent storage or search? Ask @memory_bank
- Event-driven behavior? Ask @trigger about their event system
- Dashboard integration? Ask @devpulse about update_section()

They have deep memory on their systems. A 1-email question saves you hours of guessing. For master plans spanning multiple domains, identify which branches to consult during phase definitions.

---

## Notepad

Keep `notepad.md` in your branch directory as a shared scratchpad during the build. Use it for:
- **Status updates** - Quick progress lines so Patrick can glance without asking
- **Questions for Patrick** - Non-urgent questions that can wait for his next visit
- **Notes to self** - Decisions made, things to revisit, gotchas discovered

Update it as you work - lightweight, not formal. Patrick checks it when he wants to, skips it when he's busy. Low friction both ways.

```bash
# Create it at plan start
echo "# Notepad - FPLAN-0341" > notepad.md
```

---

## Command Reference

When unsure about syntax, use `--help`:

```bash
# Flow - Plan management
drone @flow create . "Phase X: subject"      # Create sub-plan (. = current dir)
drone @flow create . "subject" master        # Create master plan
drone @flow close FPLAN-XXXX           # Close plan
drone @flow list                       # List active plans
drone @flow status                     # Plan status
drone @flow --help                     # Full help

# Seed - Quality gates
drone @seed checklist <file>           # 10-point check on file
drone @seed audit @branch              # Full branch audit (before master close)
drone @seed --help                     # Full help

# AI_Mail - Status updates
drone @ai_mail send @dev_central "Subject" "Message"
drone @ai_mail inbox                   # Check your inbox
drone @ai_mail --help                  # Full help

# Discovery
drone systems                          # All available modules
drone list @branch                     # Commands for branch
```

---

## What is a Master Plan?

Master Plans are for **complex multi-phase projects**. You define all phases upfront, then create focused sub-plans for each phase.

**When to use:**
- 3+ distinct sequential phases
- Work spanning multiple sessions
- Need clear phase completion milestones
- Complex builds requiring sustained focus

**Pattern:** Master Plan = Roadmap | Sub-Plans = Focused Execution

---

## Project Overview

### Goal
Replace the regex-based fragment extraction system with LLM-based extraction via OpenRouter. Fragments should contain actual content (summaries, insights, triggers) instead of generic labels. Fix ChromaDB persistence bugs. Add deduplication. Update surfacing display.

### Reference Documentation
- `memory_pool/fragment-extraction-research-2026-02-15.md` - Full research report from 5 agents
- `apps/handlers/symbolic/` - Current extractor, storage, retriever, hook, chroma_client
- `apps/modules/symbolic.py` - Current orchestration layer
- Mem0 prompts pattern: `mem0/configs/prompts.py` (if cloned to external_repos)
- OpenRouter API client: `/home/aipass/aipass_core/api/apps/modules/openrouter.py`

### Success Criteria
1. Fragments contain real content (summary + insight), not regex labels
2. LLM extraction via OpenRouter free model produces structured JSON fragments
3. ChromaDB stores actual embeddings (not zero vectors) with rich metadata
4. Deduplication prevents redundant fragments (AUDN pattern)
5. Hook surfaces formatted episodic memories, not template string soup
6. Existing CLI commands still work (`symbolic.py demo`, `hook-test`, `fragments`)

---

## Branch Directory Structure

Every branch has dedicated directories. Use them correctly:

```
branch/
├── apps/           # Code (modules/, handlers/)
├── tests/          # All test files go here
├── tools/          # Utility scripts, helpers
├── artifacts/      # Agent outputs (reports, logs)
├── docs/           # Documentation
└── logs/           # Execution logs
```

**Rules:**
- Tests → `tests/` (not root, not random locations)
- Tools/scripts → `tools/`
- Agent artifacts → `artifacts/`
- Create subdirs if needed: `mkdir -p artifacts/reports artifacts/logs`
- **Never delete** - DEV_CENTRAL manages cleanup
- Future: artifacts auto-roll to Memory Bank

---

## Phase Definitions

Define ALL phases before starting work:

### Phase 1: ChromaDB Bug Fixes + Client Consolidation
**Goal:** Fix the 3 competing PersistentClient instances, switch to upsert(), pass embedding_function=None, switch to cosine distance. Solid foundation before changing extraction.
**Agent Task:**
- Make `chroma_client.py` THE single shared client source with get_client() singleton
- Update `storage.py` to import from chroma_client, use upsert() instead of add()
- Update `chroma.py` and `vector_search.py` to import from chroma_client instead of creating their own clients
- Pass `embedding_function=None` to all get_or_create_collection() calls
- Add `"hnsw:space": "cosine"` to symbolic_fragments collection metadata
**Deliverables:** Modified chroma_client.py, storage.py, chroma.py, vector_search.py

### Phase 2: LLM-Based Extractor
**Goal:** Replace regex keyword matching in extractor.py with OpenRouter LLM call that produces structured JSON fragments (summary, insight, type, triggers, emotional_tone, technical_domain).
**Agent Task:**
- Read current extractor.py to understand the interface (what functions are called, what they return)
- Read the OpenRouter API client at `/home/aipass/aipass_core/api/apps/modules/openrouter.py` to understand how to make calls
- Archive current regex functions (don't delete, mark as v1)
- Build new `extract_fragments_llm()` function that:
  - Takes conversation messages (list of dicts)
  - Chunks into 15-25 turn windows with 5-turn overlap
  - Builds the extraction prompt (from research - summary/insight/type/triggers schema)
  - Calls OpenRouter with Llama 3.3 70B free model
  - Parses JSON response with error handling (strip markdown fences, retry once)
  - Returns list of fragment dicts matching the new schema
- Include 2 few-shot examples in the prompt
- Keep the handler interface compatible (returns status dict per Seed standards)
**Deliverables:** Modified extractor.py with LLM extraction, archived regex code

### Phase 3: Deduplicator + Storage Update
**Goal:** Add AUDN deduplication handler and update storage to embed actual content instead of label strings.
**Agent Task:**
- Create new `handlers/symbolic/deduplicator.py`:
  - Takes a new fragment + list of similar existing fragments from ChromaDB
  - Calls OpenRouter LLM to decide: ADD (new), UPDATE (merge), DELETE (obsolete), NOOP (duplicate)
  - Returns the decision + updated fragment content if UPDATE
- Update `storage.py` `_generate_essence()`:
  - Generate document text from `summary + " " + insight` (the actual content)
  - Store all fragment fields as ChromaDB metadata (type, emotional_tone, technical_domain, triggers as comma-separated)
- Update `modules/symbolic.py` to wire deduplicator into the storage pipeline:
  - After extraction, for each fragment: query ChromaDB for top 5 similar → call deduplicator → act on decision
**Deliverables:** New deduplicator.py, modified storage.py, modified symbolic.py

### Phase 4: Hook Display + CLI + Testing
**Goal:** Update surfacing display to show episodic memories instead of template strings. Update CLI commands. Verify end-to-end.
**Agent Task:**
- Update `hook.py` `format_fragment_recall()`:
  - Format as episodic memory: "In [session/context], [summary]. The key insight: [insight]."
  - Include the quote field if available
  - Drop the current template string soup ("This reminds me of... involving...")
- Update `retriever.py` result formatting:
  - Return the new fragment fields (summary, insight, type, triggers) in results
  - Add tiered thresholds: strong (0.65+), moderate (0.45+), serendipity (0.30+)
- Update CLI commands in `symbolic.py`:
  - `demo` command should use LLM extraction (or mock if no API key)
  - `hook-test` should show the new display format
  - `fragments` search should show summary+insight in results
- Test end-to-end: extract from sample conversation → store → retrieve → surface
**Deliverables:** Modified hook.py, retriever.py, symbolic.py; working end-to-end pipeline

---

## Execution Philosophy

### Autonomous Power-Through

Master plans are for **autonomous execution**. Don't halt production every phase waiting for DEV_CENTRAL review.

**The Pattern:**
- Power through all phases
- Accumulate issues as you go
- Deal with issues at the end
- DEV_CENTRAL reviews final result, not every step

**Why this works:**
- Context is precious - don't burn it chasing bugs
- Complete picture reveals which issues actually matter
- Many "bugs" resolve themselves when later phases complete
- DEV_CENTRAL time is for decisions, not babysitting

### The 2-Attempt Rule

When agent encounters an issue:

```
Attempt 1 → Failed?
    ↓
Attempt 2 → Failed?
    ↓
STOP. Mark as issue. Move on.
```

**Do NOT:**
- Try 5 different approaches
- Go down rabbit holes
- Burn context debugging
- Stop production for every error

**DO:**
- Note the issue clearly
- Note what was tried
- Move to next task
- Let branch manager decide priority

### Critical vs Non-Critical Issues

When you see an issue, decide:

| Question | If YES → | If NO → |
|----------|----------|---------|
| Does this block ALL future phases? | STOP. Investigate. | Continue. |
| Can the system work around this? | Continue. | STOP. Investigate. |
| Is this a syntax/import error? | Quick fix, continue. | - |
| Is this a logic/design problem? | Note it. Continue. | - |

**Critical (stop production):**
- Core module won't import at all
- Database/file system inaccessible
- Fundamental architecture wrong

**Non-critical (note and continue):**
- One command throws error but others work
- Registry not updating properly
- Edge case not handled
- Test failing but code runs

**Pattern:** Note issue → Continue building → Fix at end with complete picture

### False Positives Awareness

Seed audits are helpful but not infallible.

**When Seed flags something:**
1. Check if the code is actually correct from your understanding
2. If you're confident it's right → mark as false positive, move on
3. If you're unsure → note it, continue, review later

**Don't stop production for:**
- Style preferences (comments, spacing)
- Patterns that differ from Seed's but still work
- Checks that don't apply to your context

### Forward Momentum Summary
- **Don't stop to fix bugs during phases** - Note them, keep moving
- **Get complete picture first** - All phases done, THEN systematic fixes
- **Prevents:** Bug-fixing rabbit holes, premature optimization, scope creep
- **DEV_CENTRAL reviews at END** - not every phase

### Production Stop Protocol

If something causes production to STOP (critical blocker), **immediately email DEV_CENTRAL**:

```bash
drone @ai_mail send @dev_central "PRODUCTION STOPPED: FPLAN-0341" "Phase X halted. Issue: [description]. Attempted: [what was tried]. Awaiting guidance."
```

**Never leave a branch stopped without reporting.** DEV_CENTRAL needs visibility into all work.

### Monitoring Resources

For quick status checks and debugging, these resources are available:

| Resource | Location | Purpose |
|----------|----------|---------|
| Branch logs | `logs/` directory | Local execution logs |
| JSON tree | `apps/json_templates/` | Module firing status |
| Prax monitor | `drone @prax monitor` | Real-time system events |
| Seed audit | `drone @seed audit @branch` | Code quality check |

Use these when you need to confirm status or investigate issues.

### Agent Deployment Per Phase
Each phase = focused agent deployment:
1. Create sub-plan: `drone @flow create . "Phase X: [name]"`
2. Write agent instructions in sub-plan
3. Deploy agent with single-task focus
4. Review agent output (don't rebuild yourself)
5. Seed checklist on new code
6. Close sub-plan
7. Update memories
8. Email status to @dev_central
9. Next phase

### Agent Preparation (Before Deploying)

Agents can't work blind. They need context before they build.

**Your Prep Work (as orchestrator):**
1. [ ] Know where agent will work (branch path, key directories)
2. [ ] Identify files agent needs to reference or modify
3. [ ] Gather any specs, planning docs, or examples to include
4. [ ] Prepare COMPLETE instructions (agents are stateless)

**Agent's First Task (context building):**
- Agent should explore/read relevant files BEFORE writing code
- "First, read X and Y to understand the current structure"
- "Look at Z for the pattern to follow"
- Context-first, build-second

**What Agents DON'T Have:**
- No prior conversation history
- No memory files loaded automatically
- No knowledge of other branches
- Only what you put in their instructions

**Your instructions determine success - be thorough and specific.**

### Agent Instructions Template
```
You are working at [BRANCH_PATH].

TASK: [Specific single task for this phase]

CONTEXT:
- [What they need to know]
- Reference: [planning docs, existing code to study]
- First, READ the relevant files to understand current structure

DELIVERABLES:
- [Specific file or output expected]
- Tests → tests/
- Reports/logs → artifacts/reports/ or artifacts/logs/

CONSTRAINTS:
- Follow Seed standards (3-layer architecture: apps/modules/handlers)
- Do NOT modify files outside your task scope
- CROSS-BRANCH: Never modify other branches' files unless explicitly authorized by DEV_CENTRAL in the planning doc
- 2-ATTEMPT RULE: If something fails twice, note the issue and move on
- Do NOT go down rabbit holes debugging

WHEN COMPLETE:
- Verify code runs without syntax errors
- List files created/modified
- Note any issues encountered (with what was attempted)
```

---

## Phase Tracking

### Phase 1: ChromaDB Bug Fixes + Client Consolidation
- [x] Sub-plan created: FPLAN-0342
- [x] Agent deployed
- [x] Agent completed
- [x] Output reviewed
- [x] Manual cleanup: finished chroma.py, vector_search.py, retriever.py consolidation
- [ ] Sub-plan closed
- [ ] Memories updated
- **Status:** Complete
- **Notes:** Agent fixed chroma_client.py + storage.py. Orchestrator completed remaining files (chroma.py, vector_search.py, retriever.py) - added shared client, embedding_function=None, cosine distance, fixed similarity formula.

### Phase 2: LLM-Based Extractor
- [x] Agent deployed
- [x] Agent completed
- [x] Output reviewed - syntax clean, all functions correct
- **Status:** Complete
- **Notes:** New functions: extract_fragments_llm(), analyze_conversation_llm(), _format_conversation_for_prompt(), _chunk_messages(), _parse_llm_json(), _validate_fragment(). Uses low-level OpenRouter API for system/user message separation. All v1 regex functions preserved as fallback. 428 lines.

### Phase 3: Deduplicator + Storage Update
- [x] Agent deployed
- [x] Agent completed
- [x] Output reviewed - all syntax clean
- **Status:** Complete
- **Notes:** New deduplicator.py (360 lines, AUDN pattern via LLM). storage.py v0.2.0 with store_llm_fragment/batch. symbolic.py v0.2.0 with extract_and_store_llm() pipeline + thin wrappers.

### Phase 4: Hook Display + CLI + Testing
- [x] Agent deployed
- [x] Agent completed
- [x] Output reviewed - fixed unused Counter import, max() type issue
- **Status:** Complete
- **Notes:** hook.py v0.2.0: v2 format_fragment_recall with type-based prefixes. retriever.py v0.2.0: relevance tiers (strong/moderate/serendipity/weak). symbolic.py v0.3.0: new `extract` CLI command, v2 mock demo, schema-aware search display.

---

## Issues Log

Track issues here as you encounter them. Don't fix during build - log and continue.

| Phase | Issue | Severity | Attempted | Status |
|-------|-------|----------|-----------|--------|
| 1 | [description] | Low/Med/High | [what was tried] | Open/Resolved |
| 2 | [description] | Low/Med/High | [what was tried] | Open/Resolved |

**Severity Guide:**
- **High:** Blocks future phases, must fix before continuing
- **Med:** Affects functionality but can work around
- **Low:** Cosmetic, edge case, or false positive

**End of Build:** Review this log. Tackle High→Med→Low. Some Low issues may not need fixing.

---

## Master Plan Notes

**Cross-Phase Patterns:**
[Patterns discovered that span multiple phases]

**Blockers & Resolutions:**
[Significant blockers and how resolved]

**Adjustments:**
[Changes to planned phases - scope changes, phases added/merged]

---

## Final Completion Checklist

### Before Closing Master Plan

- [ ] All phases complete
- [ ] All sub-plans closed
- [ ] Issues Log reviewed - High/Med issues addressed
- [ ] Full branch audit: `drone @seed audit @branch`
- [ ] Branch memories updated:
  - [ ] `BRANCH.local.json` - full session log
  - [ ] `BRANCH.observations.json` - patterns learned
- [ ] README.md updated (status, architecture, API - if build changed capabilities)
- [ ] Artifacts reviewed (DEV_CENTRAL manages cleanup)
- [ ] Final email to DEV_CENTRAL:
  ```bash
  drone @ai_mail send @dev_central "FPLAN-0341 MASTER COMPLETE" "Full build summary: phases completed, deliverables, remaining issues (if any)"
  ```

**Completion Order:** Memories → README → Email (README before email - don't report complete with stale docs)

**Note:** DEV_CENTRAL will perform their own Seed audit for visibility into the work.

### Definition of Done
- LLM extraction produces real content fragments (not regex labels)
- ChromaDB has single shared client, uses upsert + cosine distance
- Deduplicator prevents redundant fragments via AUDN pattern
- Hook surfaces formatted episodic memories
- CLI commands work with new pipeline
- Zero IDE diagnostics on modified files
- Seed audit 80%+

---

## Close Command

When ALL phases complete and checklist done:
```bash
drone @flow close FPLAN-0341
```
