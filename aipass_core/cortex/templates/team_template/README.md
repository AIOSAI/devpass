# {{BRANCHNAME}}

**Role:** Business Team Manager - Strategy, Research, and Delegation
**Location:** `{{CWD}}`
**Profile:** Business Team Manager
**Created:** {{DATE}}

---

## How This Team Works

**Mode:** Think tank - research, plan, decide, delegate

This team does NOT build code directly. Instead:
1. **Research** - Investigate topics, gather data (research/)
2. **Ideate** - Explore concepts, brainstorm approaches (ideas/)
3. **Decide** - Make commitments, approve plans (decisions/)
4. **Brief** - Create handoff artifacts for workspace (briefs/)
5. **Delegate** - Dispatch build tasks to @{{branchname}}_ws

**Workspace:** `workspace/` contains a full builder branch (@{{branchname}}_ws) that handles all implementation.

---

## Directory Structure

```
{{AUTO_GENERATED_TREE}}
```

*Auto-generated on file structure changes*

---

## Key Directories

| Directory | Purpose |
|-----------|---------|
| `research/` | Investigation artifacts, analysis, raw findings |
| `ideas/` | Exploration, concepts, brainstorming, backlog |
| `decisions/` | Finalized commitments, approved strategies |
| `briefs/` | Delegation artifacts, workspace handoff docs |
| `workspace/` | Full builder branch (@{{branchname}}_ws) |

---

## Communication

- **Report to:** @dev_central
- **Delegate to:** @{{branchname}}_ws (workspace)
- **Collaborate with:** Other teams via The Commons

---

## Memory System

### Memory Files
- **{{BRANCHNAME}}.id.json** - Team identity and role
- **{{BRANCHNAME}}.local.json** - Session history (max 600 lines)
- **{{BRANCHNAME}}.observations.json** - Collaboration patterns (max 600 lines)

### Health Monitoring
- 🟢 **Green (Healthy):** Under 80% of limits
- 🟡 **Yellow (Warning):** 80-100% of limits
- 🔴 **Red (Critical):** Over limits (compression needed)

---

*Last Updated: {{AUTO_TIMESTAMP}}*
