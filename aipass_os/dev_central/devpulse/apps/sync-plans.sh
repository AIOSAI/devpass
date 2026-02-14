#!/bin/bash
# sync-plans.sh - Convert PLANS.central.json to plans_central.md
# Part of AIPass Central Aggregation System
# Created: 2025-11-30

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Plans Sync ===${NC}"
echo "Source: /home/aipass/aipass_os/AI_CENTRAL/PLANS.central.json"
echo "Output: /home/aipass/aipass_os/dev_central/plans_central.md"
echo ""

# First, refresh PLANS.central.json from all branches
echo "Refreshing PLANS.central.json..."
cd /home/aipass/aipass_core/flow
python3 apps/flow.py aggregate 2>/dev/null || true
echo ""

# Run the Python sync and capture output
cd /home/aipass
result=$(python3 apps/modules/dev_central.py plans-md 2>&1)

# Extract counts from result
active=$(echo "$result" | grep -oP "active_count': \K[0-9]+")
closed=$(echo "$result" | grep -oP "closed_count': \K[0-9]+")

if [ -n "$active" ]; then
    echo -e "${GREEN}Active: $active | Closed: $closed${NC}"
    echo ""
    echo -e "${GREEN}✓ Sync complete!${NC}"
    echo "Project overview: /home/aipass/aipass_os/dev_central/plans_central.md"
    echo ""
else
    echo -e "${YELLOW}$result${NC}"
fi
