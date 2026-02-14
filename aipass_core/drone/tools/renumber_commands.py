#!/home/aipass/.venv/bin/python3
"""
Command ID Renumbering Script

Renumbers all drone command IDs sequentially starting from 001.
Preserves all other command data and maintains active status.
"""

import json
from pathlib import Path
from datetime import datetime, timezone

DRONE_ROOT = Path("/home/aipass/aipass_core/drone")
COMMANDS_DIR = DRONE_ROOT / "commands"
REGISTRY_FILE = DRONE_ROOT / "drone_json" / "drone_registry.json"

def main():
    print("🔄 Command ID Renumbering Script")
    print("=" * 70)

    # Step 1: Collect all commands from all systems
    all_commands = []
    systems = []

    for system_dir in sorted(COMMANDS_DIR.iterdir()):
        if not system_dir.is_dir():
            continue

        registry_file = system_dir / "registry.json"
        if not registry_file.exists():
            continue

        system_name = system_dir.name
        systems.append(system_name)

        with open(registry_file, 'r') as f:
            registry = json.load(f)

        for registry_key, cmd_data in registry.items():
            all_commands.append({
                'system': system_name,
                'registry_key': registry_key,
                'old_id': cmd_data['id'],
                'data': cmd_data
            })

    print(f"\n📊 Found {len(all_commands)} commands across {len(systems)} systems")
    print(f"Systems: {', '.join(systems)}")

    # Step 2: Sort commands by system name, then by registry key
    all_commands.sort(key=lambda x: (x['system'], x['registry_key']))

    # Step 3: Assign new sequential IDs
    print("\n🔢 Renumbering commands...")
    id_mapping = {}  # old_id -> new_id

    for new_id, cmd in enumerate(all_commands, start=1):
        old_id = cmd['old_id']
        id_mapping[old_id] = new_id
        cmd['new_id'] = new_id

        if old_id != new_id:
            print(f"  {cmd['system']:15} {cmd['registry_key']:30} {old_id:03d} → {new_id:03d}")

    # Step 4: Update all registry.json files
    print("\n💾 Updating registry files...")
    for system_name in systems:
        system_dir = COMMANDS_DIR / system_name
        registry_file = system_dir / "registry.json"

        with open(registry_file, 'r') as f:
            registry = json.load(f)

        # Update IDs
        for registry_key, cmd_data in registry.items():
            old_id = cmd_data['id']
            new_id = id_mapping.get(old_id, old_id)
            cmd_data['id'] = new_id

        # Save updated registry
        with open(registry_file, 'w') as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)

        print(f"  ✅ Updated {system_name}/registry.json")

    # Step 5: Update all active.json files
    print("\n💾 Updating active command files...")
    for system_name in systems:
        system_dir = COMMANDS_DIR / system_name
        active_file = system_dir / "active.json"

        if not active_file.exists():
            continue

        with open(active_file, 'r') as f:
            active_data = json.load(f)

        # Update IDs in active commands
        for drone_cmd, cmd_info in active_data.items():
            old_id = cmd_info['id']
            new_id = id_mapping.get(old_id, old_id)
            cmd_info['id'] = new_id

        # Save updated active file
        with open(active_file, 'w') as f:
            json.dump(active_data, f, indent=2, ensure_ascii=False)

        print(f"  ✅ Updated {system_name}/active.json")

    # Step 6: Update global ID counter
    print("\n💾 Updating global ID counter...")
    with open(REGISTRY_FILE, 'r') as f:
        drone_registry = json.load(f)

    old_counter = drone_registry.get('global_id_counter', 0)
    new_counter = len(all_commands)

    drone_registry['global_id_counter'] = new_counter
    drone_registry['last_updated'] = datetime.now(timezone.utc).isoformat()

    with open(REGISTRY_FILE, 'w') as f:
        json.dump(drone_registry, f, indent=2, ensure_ascii=False)

    print(f"  ✅ Global counter: {old_counter} → {new_counter}")

    # Summary
    print("\n" + "=" * 70)
    print("✅ Renumbering complete!")
    print(f"\n📊 Summary:")
    print(f"  Total commands: {len(all_commands)}")
    print(f"  ID range: 001 to {len(all_commands):03d}")
    print(f"  Systems updated: {len(systems)}")
    print(f"\n💡 Run 'drone list' to verify the changes")

if __name__ == "__main__":
    main()
