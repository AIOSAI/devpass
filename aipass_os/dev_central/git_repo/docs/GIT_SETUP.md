# Git Setup Instructions for AIPass

## Initial Git Configuration

Before making your first commit, configure your git identity:

```bash
# Set your git username
git config --global user.name "Your Name"

# Set your git email (use your GitHub email)
git config --global user.email "your.email@example.com"

# Verify the configuration
git config --global --list
```

## Repository Setup

### 1. Initialize and Connect to GitHub

```bash
# Navigate to AIPass directory
cd /home/aipass

# Initialize git repository
git init

# Add GitHub remote
git remote add origin https://github.com/AIOSAI/AIPass.git

# Verify remote setup
git remote -v
```

### 2. Handle Nested Repositories

If you encounter warnings about embedded git repositories:

```bash
# Remove nested .git directory (example: whisper-writer)
rm -rf speakeasy/whisper-writer/.git

# Re-add the directory as regular files
git add speakeasy/whisper-writer
```

### 3. Stage and Commit

```bash
# Stage all files
git add .

# Create initial commit
git commit -m "Initial AIPass system commit

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Rename branch to main
git branch -M main

# Push to GitHub
git push -u origin main
```

## Common Issues

### CRLF → LF Warnings

These warnings are normal when migrating from Windows to Linux:
```
warning: in the working copy of 'file.md', CRLF will be replaced by LF
```

Git automatically converts Windows line endings (CRLF) to Linux line endings (LF). This is expected and harmless.

### No Email/Name Configured

Error: `fatal: no email was given and auto-detection is disabled`

**Solution:** Run the git configuration commands at the top of this document.

### Embedded Repository Warning

Warning: `adding embedded git repository: path/to/nested/repo`

**Solution:** Remove the nested `.git` directory as shown in step 2 above.

## GitHub Repository

- **URL:** https://github.com/AIOSAI/AIPass.git
- **Location:** /home/aipass/
- **Branch:** main

## Notes

- Patrick manages all git commits per AIPass workflow
- Branches handle memory files, Patrick handles git operations
- Only commit when explicitly requested
- Always verify remote setup before pushing
