#!/bin/bash
# sync-dev-local.sh - Aggregate branch dev.local files into project overview
# Part of AIPass Development Tracking System
# Created: 2025-10-18

set -e  # Exit on error

# Configuration
SEARCH_ROOT="${1:-/home/aipass}"
OUTPUT_DIR="/home/aipass/aipass_os/dev_central"
PROJECT_DEV="$OUTPUT_DIR/devpulse.central.md"
TEMP_FILE=$(mktemp)
MANUAL_SECTION_FILE=$(mktemp)

# Cleanup temp files on exit
trap 'rm -f "$TEMP_FILE" "$MANUAL_SECTION_FILE"' EXIT

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== dev.local Sync ===${NC}"
echo "Search Root: $SEARCH_ROOT"
echo "Output: $PROJECT_DEV"
echo ""

# Extract existing manual section if PROJECT file exists
if [ -f "$PROJECT_DEV" ]; then
    echo -e "${YELLOW}Preserving existing manual notes...${NC}"
    # Extract everything between ## MANUAL NOTES and ## BRANCH DEVELOPMENT TRACKING
    # Then remove ONLY trailing empty lines and separators (preserve content in middle)
    sed -n '/^## MANUAL NOTES/,/^## BRANCH DEVELOPMENT TRACKING/p' "$PROJECT_DEV" | head -n -1 | sed -e :a -e '/^\n*$/d' > "$MANUAL_SECTION_FILE.tmp"

    # Remove trailing --- and empty lines only
    awk '{lines[NR]=$0} END {
        # Find last non-empty, non-separator line
        last=0
        for(i=NR; i>=1; i--) {
            if(lines[i] !~ /^(---|[ \t]*)$/) {
                last=i
                break
            }
        }
        # Print from start to last meaningful line, plus one blank line
        for(i=1; i<=last; i++) print lines[i]
        print ""
    }' "$MANUAL_SECTION_FILE.tmp" > "$MANUAL_SECTION_FILE"

    rm -f "$MANUAL_SECTION_FILE.tmp"

    # If manual section is empty (only header or no content), create placeholder
    if [ $(wc -l < "$MANUAL_SECTION_FILE") -le 2 ]; then
        cat > "$MANUAL_SECTION_FILE" << 'EOF'
## MANUAL NOTES (Project-Wide)

[Your project-wide notes here - this section is preserved during sync]

EOF
    fi
else
    echo -e "${YELLOW}Creating new devpulse.md...${NC}"
    # Create default manual section for first-time creation
    cat > "$MANUAL_SECTION_FILE" << 'EOF'
## MANUAL NOTES (Project-Wide)

[Your project-wide notes here - this section is preserved during sync]

EOF
fi

# Start building the new PROJECT file
cat > "$TEMP_FILE" << EOF
# devpulse.central.md - AIPass Development Overview
\`\`\`
Search Root: $SEARCH_ROOT
Output: $PROJECT_DEV
Last Sync: $(date +"%Y-%m-%d %H:%M:%S")
\`\`\`

**Purpose:** Aggregated view of all branch development tracking.
**Source:** Auto-generated from branch DEV.local.md files.
**Usage:** Edit branch DEV.local.md files, then run sync to update this overview.

---
EOF

# Add preserved manual section
cat "$MANUAL_SECTION_FILE" >> "$TEMP_FILE"

# Find all dev.local.md files across AIPass
# Exclude: backups, archives, .local (trash), .backup, .vscode, templates, deleted_branches
# Sort case-insensitive by basename (branch name)
branch_files=$(find "$SEARCH_ROOT" -name "dev.local.md" -type f \
    ! -path "*/backups/*" \
    ! -path "*/archive/*" \
    ! -path "*/.local/*" \
    ! -path "*/.backup/*" \
    ! -path "*/.vscode/*" \
    ! -path "*/templates/*" \
    ! -path "*/.archive/*" \
    ! -path "*/deleted_branches/*" \
    2>/dev/null | while read -r file; do
    basename_dir=$(basename "$(dirname "$file")" | tr '[:upper:]' '[:lower:]')
    echo "$basename_dir|$file"
done | sort -t'|' -k1,1 | cut -d'|' -f2)

if [ -z "$branch_files" ]; then
    echo -e "${YELLOW}No branch DEV.local.md files found.${NC}"
    cat >> "$TEMP_FILE" << 'EOF'

---
## BRANCH DEVELOPMENT TRACKING

*No branch dev.local.md files found. Create them in branch directories to track development.*

EOF
else
    # Count branches
    branch_count=$(echo "$branch_files" | wc -l)
    echo -e "${GREEN}Found $branch_count branch DEV.local.md file(s)${NC}"
    echo ""

    # Add branch tracking section header (no TOC)
    cat >> "$TEMP_FILE" << 'EOF'

---
## BRANCH DEVELOPMENT TRACKING

EOF

    # Process each branch file with collapsible sections
    while IFS= read -r branch_file; do
        # Extract branch info
        branch_dir=$(dirname "$branch_file")
        branch_name=$(basename "$branch_dir")

        # Get last modified timestamp
        last_modified=$(stat -c %y "$branch_file" 2>/dev/null | cut -d'.' -f1)

        # Get relative path for display and linking
        rel_path=${branch_file#$SEARCH_ROOT/}

        # Create anchor-safe ID
        branch_id=$(echo "$branch_name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g' | sed 's/--*/-/g')

        echo -e "${BLUE}  ├─ $branch_name${NC} ($rel_path)"

        # Add collapsible branch section with clickable source link (using vscode:// URI to open in editor)
        cat >> "$TEMP_FILE" << EOF

<details id="$branch_id">
<summary><strong>$branch_name</strong></summary>

**Source:** [$rel_path](vscode://file$branch_file)
**Last Modified:** $last_modified

EOF

        # Add branch file content (skip metadata header)
        # Find first --- separator and start from there
        # Convert markdown headers to bold text to prevent nested collapsible sections
        # This removes ## and converts to **bold** to avoid VS Code creating sub-dropdowns
        awk '/^---$/{found=1; next} found' "$branch_file" | sed 's/^## \(.*\)$/\n**\1**\n/' >> "$TEMP_FILE"

        # Close collapsible section
        cat >> "$TEMP_FILE" << 'EOF'

</details>

EOF

    done <<< "$branch_files"
fi

# Move temp file to final location
mv "$TEMP_FILE" "$PROJECT_DEV"

echo ""
echo -e "${GREEN}✓ Sync complete!${NC}"
echo "Project overview: $PROJECT_DEV"
echo ""
