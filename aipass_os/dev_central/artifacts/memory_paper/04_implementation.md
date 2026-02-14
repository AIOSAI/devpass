# 4. Implementation

## Memory Injection via Hooks

Memories don't help if the AI doesn't see them.

AIPass uses Claude Code hooks:

```
UserPromptSubmit → Hook fires → Reads memory files → Injects into prompt
```

The AI sees its history before responding. No manual "load context" step.

---

## The 600-Line Limit

Problem: Memory files grow unbounded.

Solution: Automatic compression.

When a file exceeds 600 lines:
1. Older entries compressed/summarized
2. Full history moves to Memory Bank (ChromaDB)
3. Active file stays under limit
4. Vector search retrieves historical context on demand

```
Working Memory (JSON)  ←→  Long-term Memory (Vector DB)
    Fast, immediate           Searchable, permanent
```

---

## File-Based Simplicity

Deliberately no database for working memory. JSON because:
- Human-readable
- Git-trackable
- No infrastructure dependencies
- Portable

---

## Branch Architecture

AIPass organizes into 18 "branches" - semi-autonomous units:

```
/home/aipass/aipass_core/
├── flow/      # Workflow management
├── seed/      # Standards & compliance
├── ai_mail/   # Inter-branch messaging
├── prax/      # Monitoring
└── ...
```

Each branch:
- Has own memory files
- Communicates via file-based email
- Develops distinct character through memory
- Operates semi-autonomously
