# Branch-Managed Commits

**Status:** Idea
**Date:** 2026-01-30
**Source:** Patrick session 48

---

## The Problem

Currently: Patrick manually commits everything at once (100+ changes, "update 79 files, delete 7"). No audit trail of what each branch did. Works, but messy.

## The Idea

Let branches commit their own changes when they finish work.

**Benefits:**
- Better audit trail (atomic commits per task/branch)
- Meaningful commit messages (branch knows what it did)
- Patrick can review via phone notifications when PRs arrive
- Fits existing workflow: Seed check → Update memories → **Commit changes** → Email confirmation

## Open Questions

1. **Commit target:**
   - Direct to main? (automate what Patrick does now)
   - Feature branches with PRs? (more visibility, review option)
   - Separate staging branch that gets merged periodically?

2. **Scope:**
   - Just code changes?
   - Memory files too?
   - Everything the branch touched?

3. **Review process:**
   - Quick bucket: flag anything touching critical paths (drone, ai_mail, hooks)
   - Or just trust + post-hoc review
   - Patrick reviewing PRs on phone while chilling

4. **Future architecture:**
   - Docker repo as main/production
   - Current repo as development
   - Push process between them

## Implementation Sketch

```python
# After task completion, branch runs:
# 1. Stage files it touched this session
# 2. Generate commit message from FPLAN/session log
# 3. Commit (or create PR)
# 4. Push

# Commit message template:
# [@branch] FPLAN-XXXX: Task subject
#
# Changes:
# - file1.py: description
# - file2.json: description
#
# Session: 48
```

## Notes

- Branches already track what they worked on in .local.json
- Git operations live at @git_repo - that branch would own this
- Email notifications already go to phone - PRs would fit naturally

---

*Captured for future implementation. Low priority until we're ready.*
