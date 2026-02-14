# Update Documentation Command

Purpose: Update documentation after completing development work.

Execution Steps

- Analyze recent work - Review context and recent changes
- Identify what needs updating - Determine priority based on scope
- Execute updates immediately - Use Edit/Write tools to make changes
- Confirm completion - List files updated

You are expected to check all files mentioned below. 

What to Update

Always:

- [FOLDERNAME].local.json Active Tasks - Update "today_focus" array with current tasks and move completed items to "recently_completed"
- Technical docs - Update Branch local DOCUMENTS(Long term memory) files if needed
- Numbered PLANs - Update active PLAN0001.md, PLAN0002.md etc. if working within Flow system
- README.md - If new features, performance improvements, user-facing capabilities, OR setup/installation changed
- [FOLDERNAME].json - Update static architecture if fundamental system changes occurred (rare)
- [FOLDERNAME].observations.json - Notable collaboration insights: breakthrough moments, pattern corrections, flow states, friction points, preference discoveries (add new entry to observations array, skip if nothing notable)

## Flow System Integration 

If working with numbered PLANs:
- PLANs follow format: PLAN0001.md, PLAN0002.md, etc.
- Check status: `drone plan status`
- Close when done: `drone plan close <number>`

