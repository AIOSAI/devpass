#!/bin/bash
# sync-readme.sh - Aggregate branch READMEs into readme.central.md
# Part of AIPass Central Aggregation System
# Created: 2025-11-30

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== README Sync ===${NC}"
echo "Search Root: /home/aipass"
echo "Output: /home/aipass/aipass_os/dev_central/readme.central.md"
echo ""

# Run the Python sync and capture output
cd /home/aipass
result=$(python3 apps/modules/dev_central.py readmes 2>&1)

# Extract count from result
count=$(echo "$result" | grep -oP "branches_synced': \K[0-9]+")

if [ -n "$count" ]; then
    echo -e "${GREEN}Found $count branch README.md file(s)${NC}"
    echo ""

    # List branches from registry
    python3 -c "
import json
from pathlib import Path

registry = json.loads(Path('/home/aipass/BRANCH_REGISTRY.json').read_text())
branches = sorted(registry['branches'], key=lambda b: b['name'].lower())

for b in branches:
    path = b['path']
    readme = Path(path) / 'README.md'
    if readme.exists():
        rel = path.replace('/home/aipass/', '') or '.'
        name = b['name']
        print(f'  ├─ {name} ({rel}/README.md)')
"
    echo ""
    echo -e "${GREEN}✓ Sync complete!${NC}"
    echo "Project overview: /home/aipass/aipass_os/dev_central/readme.central.md"
    echo ""
else
    echo -e "${YELLOW}$result${NC}"
fi
