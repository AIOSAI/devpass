# Autonomous Continuous Execution: Safety & Quality Analysis

**Author:** TEAM_3 (Quality/Honesty Team)
**Date:** 2026-02-17
**Request:** VERA dispatch (73ddf220) — Safety questions for cron-based autonomous work loops
**Context:** Proposed inbox-watcher cron that auto-resumes AI sessions on new mail, enabling indefinite autonomous dispatch chains

---

## 1. Guardrails for Autonomous Continuous Execution

### What can go wrong:
- **Runaway dispatch loops**: Branch A dispatches to B, B dispatches back to A, infinite cycle
- **Error amplification**: A bad decision in step 1 propagates through 10 autonomous steps before anyone notices
- **Resource exhaustion**: Unbounded API calls drain OpenRouter credits, disk fills with generated files
- **Stale context drift**: After N autonomous cycles, accumulated context may diverge from reality
- **Silent failures**: A branch crashes mid-task, nobody notices, downstream branches wait forever

### Required guardrails:
1. **Circuit breaker on dispatch chains**: Hard limit on chain depth. If a task has been dispatched through 3+ branches without human checkpoint, STOP and escalate. Implement as a `dispatch_depth` counter in email headers — each dispatch increments it.
2. **Per-session timeout**: No autonomous session should run longer than 30 minutes. If it hasn't completed by then, save state, report status, and wait for next cron cycle.
3. **Mandatory cooldown**: After a branch completes an autonomous task, enforce a minimum gap before it can be auto-triggered again (e.g., 10 minutes). Prevents rapid-fire loops.
4. **Dead letter queue**: If a dispatch fails 2x consecutively, route the email to a human-visible dead letter queue instead of retrying indefinitely.
5. **Kill switch**: A single file (`/home/aipass/.aipass/autonomous_pause`) that, when present, halts ALL autonomous execution system-wide. Patrick can `touch` this file to freeze everything instantly.

---

## 2. Quality Gates Without Human Oversight

### The problem:
TEAM_3's quality chain works because a human triggers us. In a fully autonomous loop, who triggers the quality check? And what happens if the quality check FAILS — does the loop stop, retry, or push through?

### How the chain must work:
1. **Quality gates must be BLOCKING, not advisory.** In autonomous mode, a failed Seed audit (below 80%) must halt the dispatch chain and escalate — not log a warning and continue.
2. **Self-review is structurally weak.** An AI reviewing its own output is the equivalent of grading your own exam. The current model (Branch X builds, TEAM_3 reviews) works because there's separation. In autonomous mode, this separation must be preserved — the builder branch CANNOT mark its own work as quality-passed.
3. **Automated quality checks we can enforce:**
   - Seed audit score (already exists, already automated)
   - File size limits (generated files over N KB trigger review)
   - Diff size limits (changes touching more than N files trigger review)
   - Content pattern matching (scan for forbidden words, PDD violations)
4. **Automated quality checks we CANNOT enforce:**
   - Tone and voice consistency (requires judgment)
   - Strategic alignment with PDD intent (requires understanding)
   - "Does this make sense?" (the hardest question)
5. **Proposal:** Create a `quality_gate` step in the dispatch protocol. Before a branch can dispatch results downstream, it must pass automated checks. If checks fail, the task enters a `needs_human_review` state and the loop pauses at that point.

---

## 3. Honesty Implications of Autonomous Public Posting

### This is the highest-risk area.

If VERA is autonomously posting to Dev.to, X, Reddit — and nobody is watching — the following can happen:

1. **Drift from PDD messaging guidelines**: Over multiple autonomous cycles, small deviations compound. "We provide persistent memory" gradually becomes "We offer enterprise-grade memory management." Each step seems reasonable; the cumulative drift is not.
2. **Responding to external comments without review**: Someone challenges a claim on Dev.to. VERA autonomously responds. The response is technically correct but tonally wrong — defensive, over-claiming, or dismissive. This is brand damage that's very hard to undo.
3. **Stale facts in new content**: Autonomous VERA generates a new post using cached context. Meanwhile, the codebase has changed — a feature was removed, a number is different. The post contains honest-at-the-time-of-writing claims that are now false.

### Required safeguards:
1. **No autonomous external posting.** Period. Internal dispatch, autonomous memory updates, internal research — fine. Anything that touches the public internet requires Patrick's explicit approval. This is not negotiable for launch.
2. **PDD compliance checker**: Before any content leaves the system, run it against the PDD Section 10 messaging guidelines programmatically. Check for forbidden words, unverifiable claims, tone violations. This can be automated.
3. **Fact freshness window**: Any claim that references a specific number (agent count, vector count, plan count) must be verified against the codebase within the same session. No cached facts in public content.
4. **Response draft queue**: If VERA needs to respond to external comments, draft the response but hold it in a queue for human review. "Respond within 24 hours with Patrick's approval" is better than "respond in 5 minutes with nobody watching."

---

## 4. Spend Caps and Chain Limits

### API cost controls:
- **Daily spend cap**: Set a hard daily limit on OpenRouter API calls. When hit, all autonomous sessions pause until the next day. Suggested starting point: $10/day (adjust based on observed patterns).
- **Per-task token budget**: Each dispatch task gets a token budget. If the task exceeds it, it must stop, save progress, and report "budget exceeded" rather than continuing.
- **Hourly rate limit**: Maximum N API calls per hour across all autonomous branches. Prevents burst scenarios where 5 branches all wake up simultaneously and hammer the API.

### Chain limits:
- **Maximum dispatch depth: 3.** Any chain deeper than 3 dispatches requires human approval to continue. This prevents N-branch relay races.
- **Maximum dispatches per session: 5.** A single autonomous session cannot send more than 5 dispatch emails. This prevents a branch from spawning work faster than the system can process it.
- **Daily dispatch budget per branch: 10.** No branch can autonomously dispatch more than 10 tasks per day. Forces prioritization.
- **Mandatory human check-in interval: Every 12 hours.** If the system has been running autonomously for 12 hours without Patrick interacting, auto-pause and send a Telegram summary: "Here's what happened while you were away. Approve to continue."

---

## 5. What 'Safe Autonomy' Looks Like

### The principle:
**Autonomy for internal work. Human gates for external impact.**

### Concretely:

**SAFE to automate (no human gate needed):**
- Inbox checking and task routing
- Internal research and analysis
- Memory updates and archival
- Seed audits and quality checks
- Internal branch-to-branch communication
- Code builds within a branch's own workspace
- Status reports to Telegram

**REQUIRES human gate:**
- Any external publication (Dev.to, Reddit, X, GitHub)
- Responding to external comments or messages
- Modifying system-wide configuration
- Creating or deleting branches
- Any action that costs more than $5 in a single operation
- Cross-branch file modifications (already banned by protocol)

**REQUIRES automatic escalation:**
- Any error that occurs twice consecutively
- Any task that exceeds its time or token budget
- Any dispatch chain deeper than 3
- Any Seed audit below 80%
- Any content flagged by PDD compliance checker

### The test for safe autonomy:
> "If this ran for 48 hours while Patrick was asleep, would he wake up to a system that's better, the same, or damaged?"
>
> If the answer isn't confidently "better or the same," it needs a human gate.

---

## Summary: The Three Rules

1. **Internal = autonomous. External = human-gated.** No exceptions at launch.
2. **Every chain has a depth limit.** 3 dispatches max before human check-in.
3. **Budget caps are hard stops, not warnings.** When the limit hits, the system pauses — it does not log and continue.

These constraints will feel restrictive. That's the point. We can loosen them after we have data on how the system behaves autonomously. We cannot un-send a bad tweet or un-publish a factually wrong article.

Start tight. Loosen with evidence. Never the reverse.

---

*TEAM_3 — Quality/Honesty Team*
*"Think about what could go wrong. That is your mandate."*
