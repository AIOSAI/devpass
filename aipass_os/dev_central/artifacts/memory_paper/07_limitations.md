# 7. Limitations

What we haven't solved.

---

## Current Issues

**Cross-branch identity confusion**
Occasionally, spawned agents get confused about which branch they're at. Memory files help, but cwd detection can fail.

**Memory staleness**
Old patterns may no longer be relevant. No automatic "forgetting" or relevance decay.

**Compression loses nuance**
When memories compress at 600 lines, summarization loses detail. Important context can get flattened.

**Arbitrary thresholds**
600 lines is arbitrary. No semantic understanding of what's important vs. routine.

---

## Future Directions

**Fragmented memory**
Random memory fragments surfacing during work - like human recall. Not everything retrieved explicitly.

**Memory health monitoring**
Detecting when memories are stale, contradictory, or corrupted.

**Proactive memory**
AI suggesting what should be remembered vs. forgotten. Active curation.

**Cross-branch memory**
Shared context between branches without duplication or conflicts.
