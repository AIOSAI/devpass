# Testing the Full Workflow

This demonstrates the complete scan → reg → activate flow.

## Step 1: Scan a module

```bash
cd /home/aipass/drone
python3 drone.py scan tests/test_modules/subparsers.py
```

**Output**:
```
======================================================================
Scanning: tests/test_modules/subparsers.py
======================================================================

✅ Commands detected via argparse:

Letter  Command             Description
------  ------------------  ----------------------------------------
a       create              Create a new item
b       list                List all items
c       delete              Delete an item
d       status              Show status information

4 commands found

💡 Use 'drone reg <module>' to register commands
```

## Step 2: Register the module

```bash
python3 drone.py reg tests/test_modules/subparsers.py
```

**Output**:
```
======================================================================
Registering: subparsers
======================================================================

✅ Commands registered:

ID    Command             Status         Description
----  ------------------  -------------  ----------------------------------------
001   create              NEW            Create a new item
002   list                NEW            List all items
003   delete              NEW            Delete an item
004   status              NEW            Show status information

4 new commands registered
Registry: /home/aipass/drone/commands/subparsers/registry.json
```

## Step 3: Activate commands interactively

```bash
python3 drone.py activate subparsers
```

**Interactive Session**:
```
======================================================================
Activate commands for: subparsers
======================================================================

ID    Command             Active    Drone Command
----  ------------------  --------  ------------------------------
001   create              No        n/a
002   list                No        n/a
003   delete              No        n/a
004   status              No        n/a

0 active / 4 total

Enter command ID to activate (or 'done' to finish): 1

──────────────────────────────────────────────────────────────────────
Activating ID 001: create
──────────────────────────────────────────────────────────────────────
Drone command name (e.g., 'test create', 'backup snap'): test create
Description (optional, press Enter to skip): Create test item
✅ Activated 001 as 'drone test create'

======================================================================
Activate commands for: subparsers
======================================================================

ID    Command             Active    Drone Command
----  ------------------  --------  ------------------------------
001   create              YES       test create
002   list                No        n/a
003   delete              No        n/a
004   status              No        n/a

1 active / 4 total

Enter command ID to activate (or 'done' to finish): 2

──────────────────────────────────────────────────────────────────────
Activating ID 002: list
──────────────────────────────────────────────────────────────────────
Drone command name (e.g., 'test create', 'backup snap'): test list
Description (optional, press Enter to skip):
✅ Activated 002 as 'drone test list'

======================================================================
Activate commands for: subparsers
======================================================================

ID    Command             Active    Drone Command
----  ------------------  --------  ------------------------------
001   create              YES       test create
002   list                YES       test list
003   delete              No        n/a
004   status              No        n/a

2 active / 4 total

Enter command ID to activate (or 'done' to finish): done

======================================================================
Activation Summary: subparsers
======================================================================

ID    Command             Drone Command            Description
----  ------------------  -----------------------  ------------------------------
001   create              test create              Create test item
002   list                test list                List all items

✅ 2 commands activated

You can now use:
  drone test create
  drone test list
```

## Files Created

After activation, these files exist:

### /home/aipass/drone/commands/subparsers/registry.json
```json
{
  "create": {
    "id": 1,
    "help": "Create a new item",
    "module_path": "tests/test_modules/subparsers.py",
    "registered_date": "2025-10-16T04:11:16.237142+00:00",
    "active": true,
    "drone_command": "test create",
    "description": "Create test item"
  },
  "list": {
    "id": 2,
    "help": "List all items",
    "module_path": "tests/test_modules/subparsers.py",
    "registered_date": "2025-10-16T04:11:16.237150+00:00",
    "active": true,
    "drone_command": "test list",
    "description": "List all items"
  },
  "delete": {
    "id": 3,
    "help": "Delete an item",
    "module_path": "tests/test_modules/subparsers.py",
    "registered_date": "2025-10-16T04:11:16.237154+00:00",
    "active": false
  },
  "status": {
    "id": 4,
    "help": "Show status information",
    "module_path": "tests/test_modules/subparsers.py",
    "registered_date": "2025-10-16T04:11:16.237157+00:00",
    "active": false
  }
}
```

### /home/aipass/drone/commands/subparsers/active.json
```json
{
  "test create": {
    "id": 1,
    "command_name": "create",
    "description": "Create test item",
    "module_path": "tests/test_modules/subparsers.py"
  },
  "test list": {
    "id": 2,
    "command_name": "list",
    "description": "List all items",
    "module_path": "tests/test_modules/subparsers.py"
  }
}
```

## What's Next

Phase 4-8 will:
- Make `drone test create` actually execute the command
- Add `drone list` and `drone systems` commands
- Build command execution bridge
- Complete the workflow
