#!/bin/bash

# List of main entry points
files=(
    "/home/aipass/aipass_core/ai_mail/apps/ai_mail.py"
    "/home/aipass/aipass_core/api/apps/api.py"
    "/home/aipass/aipass_core/backup_system/apps/backup_system.py"
    "/home/aipass/aipass_core/cli/apps/cli.py"
    "/home/aipass/aipass_core/cortex/apps/cortex.py"
    "/home/aipass/aipass_core/devpulse/apps/devpulse.py"
    "/home/aipass/aipass_core/drone/apps/drone.py"
    "/home/aipass/aipass_core/flow/apps/flow.py"
    "/home/aipass/aipass_core/prax/apps/prax.py"
    "/home/aipass/seed/apps/seed.py"
)

echo "Checking main functions in all entry points..."
echo

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "=== $(basename $file) ==="
        grep -n "^def " "$file" | head -3
        echo
    fi
done
