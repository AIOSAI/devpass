#!/usr/bin/env python3
"""Quick test to show actual backup path calculation"""

from pathlib import Path

# Simulate config_handler.py calculation
config_file = Path("/home/aipass/aipass_core/backup_system/apps/handlers/config/config_handler.py")
print(f"Config file location: {config_file}")
print(f"  parent:               {config_file.parent}")
print(f"  parent.parent:        {config_file.parent.parent}")
print(f"  parent.parent.parent: {config_file.parent.parent.parent}")

BASE_BACKUP_DIR = str(config_file.parent.parent.parent / "backups")
print(f"\nBASE_BACKUP_DIR = {BASE_BACKUP_DIR}")

# Simulate mode destination
BACKUP_DESTINATIONS = {
    "system_snapshot": f"{BASE_BACKUP_DIR}",
    "versioned_backup": f"{BASE_BACKUP_DIR}",
}

# Simulate BACKUP_MODES
BACKUP_MODES = {
    'snapshot': {
        'name': 'System Snapshot',
        'destination': BACKUP_DESTINATIONS["system_snapshot"],
        'folder_name': 'system_snapshot',
    },
    'versioned': {
        'name': 'Versioned Backup',
        'destination': BACKUP_DESTINATIONS["versioned_backup"],
        'folder_name': 'versioned_backup',
    },
}

# Simulate BackupEngine.__init__
for mode in ['snapshot', 'versioned']:
    print(f"\n{'='*60}")
    print(f"Mode: {mode}")
    mode_config = BACKUP_MODES[mode]
    backup_dest = Path(mode_config['destination'])
    backup_folder_name = mode_config['folder_name']
    backup_path = backup_dest / backup_folder_name
    
    print(f"  mode_config['destination']: {mode_config['destination']}")
    print(f"  backup_dest:                {backup_dest}")
    print(f"  backup_folder_name:         {backup_folder_name}")
    print(f"  FINAL backup_path:          {backup_path}")
    print(f"  Absolute path:              {backup_path.absolute()}")
