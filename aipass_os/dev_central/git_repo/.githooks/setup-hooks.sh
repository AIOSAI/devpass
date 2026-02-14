#!/bin/bash
# Setup git hooks for AIPass Ecosystem

echo "Setting up git hooks..."

# Create symlink or copy pre-commit hook
if [ -f .git/hooks/pre-commit ]; then
    echo "Backing up existing pre-commit hook to .git/hooks/pre-commit.backup"
    mv .git/hooks/pre-commit .git/hooks/pre-commit.backup
fi

# Copy the hook (symlinks don't work well on Windows)
cp .githooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

echo "✅ Git hooks installed successfully!"
echo ""
echo "The pre-commit hook will:"
echo "  - Check Python files with pyright"
echo "  - Check TypeScript files with tsc in their respective projects"
echo ""
echo "To bypass hooks temporarily, use: git commit --no-verify"