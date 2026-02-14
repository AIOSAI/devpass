# devpulse.central.md - AIPass Development Overview
```
Search Root: /home/aipass
Output: /home/aipass/aipass_os/dev_central/devpulse.central.md
Last Sync: 2025-12-08 10:00:32
```

**Purpose:** Aggregated view of all branch development tracking.
**Source:** Auto-generated from branch DEV.local.md files.
**Usage:** Edit branch DEV.local.md files, then run sync to update this overview.

---
## MANUAL NOTES (Project-Wide)
[Your project-wide notes here - this section is preserved during sync]


---
## BRANCH DEVELOPMENT TRACKING


<details id="ai-mail">
<summary><strong>ai_mail</strong></summary>

**Source:** [aipass_core/ai_mail/dev.local.md](vscode://file/home/aipass/aipass_core/ai_mail/dev.local.md)
**Last Modified:** 2025-12-08 09:46:59



**Issues**


-



**Upgrades**


-



**Testing**


-



**Notes**


-



**Ideas**


-


**Todos**


-

</details>


<details id="api">
<summary><strong>api</strong></summary>

**Source:** [aipass_core/api/dev.local.md](vscode://file/home/aipass/aipass_core/api/dev.local.md)
**Last Modified:** 2025-11-22 08:49:39



**Issues**


-



**Upgrades**


-



**Testing**


-



**Notes**


-



**Ideas**


-


**Todos**


-

</details>


<details id="backup-system">
<summary><strong>backup_system</strong></summary>

**Source:** [aipass_core/backup_system/dev.local.md](vscode://file/home/aipass/aipass_core/backup_system/dev.local.md)
**Last Modified:** 2025-11-13 10:50:09



**Issues**


-



**Upgrades**


-



**Testing**


-



**Notes**


-



**Ideas**


-


**Todos**


-

</details>


<details id="cli">
<summary><strong>cli</strong></summary>

**Source:** [aipass_core/cli/dev.local.md](vscode://file/home/aipass/aipass_core/cli/dev.local.md)
**Last Modified:** 2025-11-13 10:50:13



**Issues**


-



**Upgrades**


-



**Testing**


-



**Notes**


-



**Ideas**


-


**Todos**


-

</details>


<details id="cortex">
<summary><strong>cortex</strong></summary>

**Source:** [aipass_core/cortex/dev.local.md](vscode://file/home/aipass/aipass_core/cortex/dev.local.md)
**Last Modified:** 2025-11-24 06:38:36



**Issues**


- 



**Upgrades**


-



**Testing**


-



**Notes**


-



**Ideas**


-


**Todos**


-

</details>


<details id="dev-central">
<summary><strong>dev_central</strong></summary>

**Source:** [aipass_os/dev_central/dev.local.md](vscode://file/home/aipass/aipass_os/dev_central/dev.local.md)
**Last Modified:** 2025-11-30 20:18:36



**Issues**


- **Memory Bank Config Investigation** (2025-11-30)
  - Current: DEV_CENTRAL.local.json has `max_lines: 800` in file metadata, Memory Bank config has `1000`
  - File metadata takes priority, so 800 wins (by design)
  - Conflict: Two places to set limits = confusion
  - **Future goal:** Each branch should have their own local JSON config for Memory Bank settings (e.g., `branch_json/memory_config.json`) rather than one central location
  - Need to understand all the different config locations and priority order
  - Low priority - current setup works, just not ideal



**Upgrades**


-



**Testing**


-



**Notes**


-



**Ideas**


-


**Todos**


-

</details>


<details id="devpulse">
<summary><strong>devpulse</strong></summary>

**Source:** [aipass_os/dev_central/devpulse/dev.local.md](vscode://file/home/aipass/aipass_os/dev_central/devpulse/dev.local.md)
**Last Modified:** 2025-11-13 10:50:11



**Issues**


-



**Upgrades**


-



**Testing**


-



**Notes**


-



**Ideas**


-


**Todos**


-

</details>


<details id="drone">
<summary><strong>drone</strong></summary>

**Source:** [aipass_core/drone/dev.local.md](vscode://file/home/aipass/aipass_core/drone/dev.local.md)
**Last Modified:** 2025-11-29 01:57:27



**Issues**


-

- [2025-11-22 16:23] tester
- [2025-11-22 16:34] test entry
- [2025-11-25 19:55] Test current directory resolution


**Upgrades**


-

- [2025-11-25 19:55] Test @ resolution for drone branch


**Testing**


-

- [2025-11-29 01:57] Test note


**Notes**


-



**Ideas**


-


**Todos**


-

</details>


<details id="flow">
<summary><strong>flow</strong></summary>

**Source:** [aipass_core/flow/dev.local.md](vscode://file/home/aipass/aipass_core/flow/dev.local.md)
**Last Modified:** 2025-12-04 21:42:27



**Issues**


-

- [2025-11-21 23:05] test
- [2025-11-21 23:08] test from direct python call
- [2025-11-21 23:22] test
- [2025-11-21 23:30] testing
- [2025-11-22 08:25] test issue
- [2025-11-22 16:34] test entry from drone
- [2025-11-25 19:55] Testing @ resolution
- [2025-11-28 20:43] testing dashboard
- [2025-11-28 20:44] testing dashboard
- [2025-11-28 20:49] Test from Claude
- [2025-11-29 14:24] test entry
- [2025-11-29 14:25] test
- [2025-12-02 14:29] test path fix
- [2025-12-02 14:29] test
- [2025-12-02 14:30] test
- [2025-12-03 00:04] test
- [2025-12-04 21:42] testing


**Upgrades**


-



**Testing**


-



**Notes**


-



**Ideas**


-


**Todos**


-

</details>


<details id="git-repo">
<summary><strong>git_repo</strong></summary>

**Source:** [aipass_os/dev_central/git_repo/dev.local.md](vscode://file/home/aipass/aipass_os/dev_central/git_repo/dev.local.md)
**Last Modified:** 2025-11-22 18:57:53



**Issues**


-



**Upgrades**


-



**Testing**


-



**Notes**


-



**Ideas**


-


**Todos**


-

</details>


<details id="mcp-servers">
<summary><strong>mcp_servers</strong></summary>

**Source:** [mcp_servers/dev.local.md](vscode://file/home/aipass/mcp_servers/dev.local.md)
**Last Modified:** 2025-11-24 06:39:15



**Issues**


- 



**Upgrades**


-



**Testing**


-



**Notes**


-



**Ideas**


-


**Todos**


-

</details>


<details id="memory-bank">
<summary><strong>MEMORY_BANK</strong></summary>

**Source:** [MEMORY_BANK/dev.local.md](vscode://file/home/aipass/MEMORY_BANK/dev.local.md)
**Last Modified:** 2025-11-22 16:34:53



**Issues**


- Memories are not auto rolling off, see aipassbranch

- [2025-11-22 16:34] tester
- [2025-11-22 16:34] tester


**Upgrades**


-



**Testing**


-



**Notes**


-



**Ideas**


-


**Todos**


-

</details>


<details id="permissions">
<summary><strong>permissions</strong></summary>

**Source:** [aipass_os/dev_central/permissions/dev.local.md](vscode://file/home/aipass/aipass_os/dev_central/permissions/dev.local.md)
**Last Modified:** 2025-11-22 09:07:55


</details>


<details id="prax">
<summary><strong>prax</strong></summary>

**Source:** [aipass_core/prax/dev.local.md](vscode://file/home/aipass/aipass_core/prax/dev.local.md)
**Last Modified:** 2025-11-13 10:50:10



**Issues**


-



**Upgrades**


-



**Testing**


-



**Notes**


-



**Ideas**


-


**Todos**


-

</details>


<details id="projects">
<summary><strong>projects</strong></summary>

**Source:** [projects/dev.local.md](vscode://file/home/aipass/projects/dev.local.md)
**Last Modified:** 2025-11-23 13:47:28



**Issues**


-



**Upgrades**


-



**Testing**


-



**Notes**


-



**Ideas**


-


**Todos**


-

</details>


<details id="seed">
<summary><strong>seed</strong></summary>

**Source:** [seed/dev.local.md](vscode://file/home/aipass/seed/dev.local.md)
**Last Modified:** 2025-12-02 14:13:20



**Issues**


-



**Upgrades**


-



**Testing**


-



**Notes**


-



**Ideas**


-


**Todos**


-

</details>


<details id="trigger">
<summary><strong>trigger</strong></summary>

**Source:** [aipass_core/trigger/dev.local.md](vscode://file/home/aipass/aipass_core/trigger/dev.local.md)
**Last Modified:** 2025-11-30 21:14:30



**Issues**


-



**Upgrades**


-



**Testing**


-



**Notes**


-



**Ideas**


-


**Todos**


-

</details>

