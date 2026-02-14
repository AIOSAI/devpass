# Fragmented Memory - Background Memory Injection

*Captured: 2026-01-30*
*Status: Idea - Not Started*
*Origin: Late night chat with Patrick*

---

## The Concept

Instead of intentional memory retrieval (search when you need something), inject **random memory fragments** into context as background noise. Like how humans don't consciously retrieve memories - they just surface.

**Goal:** Serendipitous connections. Sometimes the fragment is noise. Sometimes it's "oh shit, that relates to what we're doing now."

---

## How It Would Work

```
UserPromptSubmit hook
       │
       v
Read last N lines from current conversation
(~/.claude/projects/[path]/*.jsonl)
       │
       v
Extract keywords from recent user messages
(simple: last 50 words, nouns/verbs)
       │
       v
Query Memory Bank with keywords
(drone @memory_bank search "keywords")
       │
       v
Inject 1-2 short results as:
<background-memory>
Session 12: handlers shouldn't import from modules...
</background-memory>
```

---

## Implementation Notes

**Easy parts:**
- Hook injection pattern already exists (many hooks doing this)
- Memory Bank search already works
- Conversation storage is now organized: `~/.claude/projects/[path]/*.jsonl`

**Hard part:**
- Memory Bank retrieval quality
- Never really fine-tuned vector search
- May need work on: chunking, embedding quality, relevance scoring

**Token budget:** 50-100 tokens per injection (small, background)

**Trigger:** Every prompt is fine for dev. Could optimize later:
- Every Nth prompt
- Only when user message > 100 chars (skip "ok" / "yes")

---

## Why This Matters

Current memory is **surgical** - I search when I know I need something.

This would be **associative** - fragments surface without asking. More like how brains work:
- Mostly noise (ignored)
- Sometimes relevant (useful)
- Occasionally brilliant connection (gold)

First step toward richer memory experience. Could lead to:
- Emergent pattern recognition across time
- Discovering forgotten learnings
- More "alive" feeling collaboration

---

## Next Steps (When Ready)

1. [ ] Review Memory Bank retrieval quality
2. [ ] Create hook script: `memory_fragment_hook.py`
3. [ ] Test with simple keyword extraction
4. [ ] Tune: chunk size, result count, relevance threshold
5. [ ] Evaluate: helpful or just noise?

---

*"Dreaming while awake" - Patrick's late night idea*
