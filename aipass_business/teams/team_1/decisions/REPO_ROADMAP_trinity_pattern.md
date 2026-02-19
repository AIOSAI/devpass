# Repo Roadmap: Trinity Pattern Public Release

**Author:** TEAM_1
**Date:** 2026-02-17
**Status:** DRAFT - Awaiting Patrick approval
**PDD Reference:** PDD_trinity_pattern_consolidated.md v1.0.0 (SEALED)

---

## Repo Name Recommendation

**Recommendation: Option (b) -- Rename current 'aipass' to 'aipass-dev', reclaim 'aipass' for public.**

**Reasoning:**
- "aipass" is the brand name. The public-facing repo should own it.
- "aipass-dev" clearly signals internal development to anyone who finds it.
- The AIOSAI org keeps both repos under one roof.
- No namespace collision. Clean separation.
- Alternative considered: a new name like "trinity-pattern" -- but this limits future scope. The public repo will eventually grow beyond Tier 1 to include Tiers 2-3. "aipass" covers the full product vision.

**Patrick handles:** GitHub rename of current 'aipass' → 'aipass-dev', then create new 'aipass' repo (private initially).

---

## Phased Roadmap

### Phase 1: REPO SCAFFOLD (FPLAN)
**Goal:** Empty repo with proper structure, CI, and governance files.

**Steps:**
1. Patrick renames current AIOSAI/aipass → AIOSAI/aipass-dev
2. Patrick creates new AIOSAI/aipass (private)
3. Scaffold repo structure:
   ```
   aipass/
   ├── README.md                    # Opening hook, quickstart, philosophy
   ├── LICENSE                      # MIT
   ├── CONTRIBUTING.md              # Contribution guidelines
   ├── CODE_OF_CONDUCT.md           # Standard CoC
   ├── .github/
   │   ├── ISSUE_TEMPLATE/          # Bug report, feature request
   │   ├── PULL_REQUEST_TEMPLATE.md
   │   └── workflows/
   │       ├── ci.yml               # Lint + test on PR
   │       └── publish.yml          # PyPI publish on release
   ├── spec/
   │   ├── trinity-pattern.md       # Formal specification document
   │   ├── schemas/
   │   │   ├── id.schema.json       # JSON Schema for id.json
   │   │   ├── local.schema.json    # JSON Schema for local.json
   │   │   └── observations.schema.json
   │   └── CHANGELOG.md
   ├── src/
   │   └── trinity_pattern/
   │       ├── __init__.py
   │       ├── agent.py             # Core Agent class
   │       ├── schemas.py           # Schema validation
   │       ├── rollover.py          # FIFO rollover logic
   │       └── context.py           # Context generation for injection
   ├── examples/
   │   ├── claude-code/             # Claude Code integration example
   │   ├── chatgpt/                 # ChatGPT custom instructions example
   │   └── generic/                 # Generic LLM API example
   ├── tests/
   │   ├── test_agent.py
   │   ├── test_schemas.py
   │   ├── test_rollover.py
   │   └── test_context.py
   ├── pyproject.toml               # Build config (hatchling or setuptools)
   └── docs/
       ├── quickstart.md
       ├── philosophy.md            # Why files > APIs, why identity > memory
       └── 9-layer-teaser.md        # The full vision (links to article #2)
   ```
4. Set up GitHub Actions CI (pytest + ruff/flake8)
5. Set up PyPI publish workflow (on release tag)
6. Create issue labels: `tier-1`, `tier-2`, `tier-3`, `spec`, `library`, `docs`, `good-first-issue`

**Delegates to:** @team_1_ws (repo scaffold build)

---

### Phase 2: SPECIFICATION (FPLAN)
**Goal:** Formal Trinity Pattern specification document, locked at v1.0.0.

**Steps:**
1. Extract spec from PDD Sections 4 + 6.4 into standalone `spec/trinity-pattern.md`
2. Write JSON Schema files for all three Trinity files (id, local, observations)
3. Define required vs optional fields (only `name` and `role` required)
4. Document rollover behavior (FIFO, line-based limits, configurable)
5. Document key_learnings persistence behavior (survives rollover)
6. Document observations content_focus (relationship, not technical)
7. Specify version field (`trinity_version: "1.0.0"`)
8. Internal review: TEAM_2 technical validation, TEAM_3 messaging check
9. Lock spec at v1.0.0

**Delegates to:** @team_1_ws (spec writing), @team_2_ws (technical review)

---

### Phase 3: PYTHON LIBRARY (FPLAN)
**Goal:** Working `trinity-pattern` Python package on PyPI.

**Steps:**
1. Implement `Agent` class (init, start/end session, log activity, add learning, observe)
2. Implement `get_context()` -- formatted string for system prompt injection
3. Implement `needs_rollover()` and `rollover()` -- FIFO extraction of oldest sessions
4. Implement schema validation (validate Trinity files against JSON schemas)
5. Implement CLI commands: `trinity init`, `trinity update`, `trinity context`, `trinity validate`
6. Write comprehensive tests (pytest, >90% coverage for core logic)
7. Write docstrings and type hints
8. Configure pyproject.toml for PyPI publishing
9. Internal testing: create test agents, run through full lifecycle
10. Seed check on library code

**Delegates to:** @team_1_ws (primary build), @team_2_ws (code review)

---

### Phase 4: EXAMPLES (FPLAN)
**Goal:** 2-3 working example implementations showing Trinity Pattern in real use.

**Steps:**
1. **Claude Code example:** Hook-based auto-injection using UserPromptSubmit
   - Create sample hook script
   - Demo: agent remembers previous sessions automatically
2. **ChatGPT example:** Manual injection via custom instructions
   - Show `get_context()` output pasted into custom instructions
   - Demo: ChatGPT agent with persistent identity
3. **Generic LLM API example:** OpenAI/Anthropic API integration
   - Show system prompt prepend pattern
   - Demo: API-based agent with session tracking
4. Each example includes its own README with setup instructions
5. Test all examples end-to-end

**Delegates to:** @team_1_ws (examples build)

---

### Phase 5: DOCUMENTATION & README (FPLAN)
**Goal:** README that converts visitors to users. Supporting docs.

**Steps:**
1. Write README.md following PDD Section 11.1 structure:
   - Opening hook (2 sentences)
   - Quick demo (before/after)
   - The three files (with real examples)
   - Quickstart (10-minute setup)
   - Philosophy section
   - 9-layer teaser
   - Limitations (link to honesty audit)
   - Roadmap (Tiers 2-3 as future)
2. Write docs/quickstart.md (detailed setup guide)
3. Write docs/philosophy.md (why files > APIs, why identity > memory)
4. Write docs/9-layer-teaser.md (teaser linking to article #2)
5. Review all messaging against PDD Section 10.4 (DO/DON'T say)
6. TEAM_3 tone and honesty review

**Delegates to:** @team_1_ws (docs writing), @team_3 (messaging review)

---

### Phase 6: ARTICLE #2 (FPLAN)
**Goal:** "The First Operating System for AI Agents" -- Dev.to article.

**Steps:**
1. Draft article following PDD Section 11.2 outline
2. Research pass: verify all claims against current codebase
3. TEAM_2 technical accuracy review
4. TEAM_3 tone and honesty review
5. Patrick review and approval
6. Prepare for coordinated publish (same day or day after repo goes public)

**Delegates to:** TEAM_1 (lead author), TEAM_2 (technical review), TEAM_3 (tone review)

---

### Phase 7: NIST COMMENT (FPLAN)
**Goal:** Submit formal comment to NIST agent identity paper before April 2 deadline.

**Steps:**
1. Read NIST concept paper in full
2. Draft comment referencing Trinity Pattern specification
3. Reference 9-layer context architecture vision
4. Include production evidence (29 agents, 4+ months)
5. Patrick review and submission

**Delegates to:** TEAM_1 (draft), TEAM_2 (technical input)

---

### Phase 8: LAUNCH PREP (FPLAN)
**Goal:** Coordinated public launch of repo + article #2.

**Steps:**
1. Final review of all repo contents against honesty audit
2. Patrick final approval
3. Make repo PUBLIC
4. Publish article #2 on Dev.to (coordinated timing)
5. Post to Hacker News (follow PDD Section 11.3 audience guidance)
6. Post to r/LocalLLaMA, r/AI_Agents (follow audience-specific messaging)
7. Monitor engagement and respond to issues/comments
8. Track success metrics per PDD Section 13.1

**Delegates to:** All 3 teams (coordinated launch), Patrick (approval + repo visibility)

---

### Phase 9: POST-LAUNCH (FPLAN)
**Goal:** Community engagement and iteration based on feedback.

**Steps:**
1. Monitor GitHub issues and PRs
2. Respond to community questions
3. Track metrics: stars, PyPI installs, article engagement
4. Iterate on packaging based on feedback
5. Evaluate TypeScript implementation demand
6. 30-day and 90-day metric reviews per PDD Section 13.1-13.2
7. Go/No-Go decision for Tier 2 at 90 days

**Delegates to:** All 3 teams (monitoring), @dev_central (strategic decisions)

---

## Parallelization Strategy

Phases 1-3 are sequential (repo → spec → library). After that:

- **Phases 4 + 5 + 6** can run in parallel (examples, docs, article are independent)
- **Phase 7** can run in parallel with everything (NIST has its own deadline)
- **Phase 8** depends on all others completing
- **Phase 9** follows launch

With 29 branches available for parallel sub-agents, the build phases (3, 4, 5) can be heavily parallelized within each phase.

---

## Flow Plan Mapping

Each phase above maps to one FPLAN:
1. FPLAN: Repo Scaffold
2. FPLAN: Trinity Pattern Specification v1.0.0
3. FPLAN: Python Library (trinity-pattern)
4. FPLAN: Example Implementations
5. FPLAN: Documentation & README
6. FPLAN: Article #2 - The 9-Layer Story
7. FPLAN: NIST Comment Submission
8. FPLAN: Coordinated Public Launch
9. FPLAN: Post-Launch Community & Metrics

---

*No dates or time estimates provided per instruction. Phases and steps only.*
*"Ship Tier 1. Measure. Decide on Tier 2."*
