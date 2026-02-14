# GIT_REPO Branch

## Purpose
Git repository management and version control operations for the AIPass ecosystem.

## Architecture
Modular architecture with auto-discovered modules:
- Main orchestrator (`apps/git_repo.py`) handles routing
- Modules in `apps/modules/` implement functionality (currently empty - ready for future modules)
- `apps/git_commands.py` - Git command cheatsheet utility
- JSON templates for configuration and data persistence
- Handlers for JSON operations

## Directory Structure
```
git_repo/
├── apps/                       # Application code
│   ├── git_repo.py             # Main orchestrator
│   ├── git_commands.py         # Git command utilities
│   ├── handlers/               # Handler modules
│   │   └── json/
│   │       └── json_handler.py
│   ├── json_templates/         # JSON templates
│   │   ├── custom/
│   │   ├── default/
│   │   │   ├── config.json
│   │   │   ├── data.json
│   │   │   └── log.json
│   │   └── registry/
│   ├── modules/                # Auto-discovered modules
│   ├── extensions/
│   └── plugins/
├── ai_mail.local/              # AI Mail messages
├── artifacts/                  # Build artifacts
├── docs/                       # Documentation
│   ├── GIT_SETUP.md
│   └── PRE_COMMIT_HOOKS_STATUS.md
├── dropbox/                    # File dropbox
├── git_repo_json/              # JSON utilities
├── logs/                       # Application logs
├── templates/                  # General templates
├── tests/                      # Test suite
├── tools/                      # Utility tools
├── .seed/                      # Seed compliance config
├── GIT_REPO.id.json            # Branch identity
├── GIT_REPO.local.json         # Session history
├── GIT_REPO.observations.json  # Collaboration patterns
├── DASHBOARD.local.json        # System status dashboard
├── dev.local.md                # DevPulse notes
├── pytest.ini                  # Pytest configuration
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Usage
```bash
# Run the main orchestrator
python3 apps/git_repo.py <command> [options]

# Get help
python3 apps/git_repo.py --help

# Git cheatsheet (standalone utility)
python3 apps/git_commands.py              # All commands
python3 apps/git_commands.py status       # Status commands
python3 apps/git_commands.py branch       # Branch commands
python3 apps/git_commands.py emergency    # Emergency fixes
```

## Module Interface
All modules must implement:
```python
def handle_command(args: argparse.Namespace) -> bool:
    """Handle command if applicable.

    Returns:
        bool: True if command was handled
    """
```

## Standards Compliance
- 100% Seed compliance (achieved 2025-11-29)
- Uses sys.path.insert(0) for imports
- Rich console for output formatting
- Structured logging with Python logger
- JSON templates for data persistence

## Memory Files
- `GIT_REPO.id.json` - Branch identity
- `GIT_REPO.local.json` - Session history
- `GIT_REPO.observations.json` - Collaboration patterns
- `DASHBOARD.local.json` - System status

## Version
v1.0.2 - 2026-01-30

## Contact
Branch: @git_repo
Location: /home/aipass/aipass_os/dev_central/git_repo/