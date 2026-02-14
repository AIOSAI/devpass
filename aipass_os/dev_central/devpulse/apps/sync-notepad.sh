#!/bin/bash
# sync-notepad.sh - Aggregate branch notepads into notepad.central.md
# Part of AIPass Central Aggregation System
# Created: 2025-11-30

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Notepad Sync ===${NC}"
echo "Search Root: /home/aipass"
echo "Output: /home/aipass/aipass_os/dev_central/notepad.central.md"
echo ""

# Run the Python sync and capture output
cd /home/aipass
result=$(python3 apps/modules/dev_central.py notepads 2>&1)

# Extract count from result
count=$(echo "$result" | grep -oP "branches_synced': \K[0-9]+")

if [ -n "$count" ]; then
    echo -e "${GREEN}Found $count branch notepad.md file(s)${NC}"
    echo ""

    # List branches from registry that have notepad.md
    python3 -c "
import json
from pathlib import Path

registry = json.loads(Path('/home/aipass/BRANCH_REGISTRY.json').read_text())
branches = sorted(registry['branches'], key=lambda b: b['name'].lower())

for b in branches:
    path = b['path']
    notepad = Path(path) / 'notepad.md'
    if notepad.exists():
        rel = path.replace('/home/aipass/', '') or '.'
        name = b['name']
        print(f'  ├─ {name} ({rel}/notepad.md)')
"
    echo ""
    echo -e "${GREEN}✓ Sync complete!${NC}"
    echo "Project overview: /home/aipass/aipass_os/dev_central/notepad.central.md"
    echo ""
else
    echo -e "${YELLOW}$result${NC}"
fi
