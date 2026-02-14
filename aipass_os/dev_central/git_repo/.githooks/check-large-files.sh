#!/bin/bash

# ========================================
# Large File Protection (Standalone)
# ========================================
# This script checks for large files in staged changes
# Can be called independently or integrated into pre-commit

echo "🔍 Checking for large files..."
max_size=104857600  # 100MB in bytes

while IFS= read -r file; do
    if [ -f "$file" ]; then
        size=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null)
        if [ "$size" -gt "$max_size" ]; then
            size_mb=$((size / 1048576))
            echo ""
            echo "❌ ERROR: $file is ${size_mb}MB (larger than 100MB limit)"
            echo "   Large files should be added to .gitignore"
            echo "   Common large files: *.img, *.iso, *.dmg, *.zip, *.tar.gz"
            echo ""
            echo "To bypass this check:"
            echo "  git commit --no-verify"
            exit 1
        fi
    fi
done < <(git diff --cached --name-only)

echo "✅ No large files detected (all files under 100MB)"
exit 0
