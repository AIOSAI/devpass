# ACL (Access Control Lists) Permissions Guide
*Technical reference for managing fine-grained file permissions for Claude Code*

## What Are ACLs?

Access Control Lists extend traditional Unix permissions (rwx) by allowing specific permissions for specific users/groups without changing ownership. Perfect for giving Claude Code surgical access to system files.

## Basic ACL Commands

### Granting Permissions

```bash
# Remove a directory and its contents
sudo rm -rf /path/to/your/folder

# Remove a single file
```bash
sudo rm /path/to/your/file.txt

```bash
# Grant user full permissions to a specific file
sudo setfacl -m u:input-x:rwx /usr/local/bin/api-connect

# Grant user permissions to a directory (create files only)
sudo setfacl -m u:input-x:rwx /usr/local

# Grant read-only access
sudo setfacl -m u:input-x:r-- /etc/some-config

# Grant read and execute (for scripts)
sudo setfacl -m u:input-x:r-x /usr/local/bin/script.sh
```

### Permission Breakdown
- `r` (read): View file contents, list directory
- `w` (write): Modify file, create/delete in directory
- `x` (execute): Run file, access directory contents
- `-` (none): No permission for that action

### Recursive Permissions (USE WITH CAUTION)

```bash
# Grant permissions to directory AND all contents
sudo setfacl -R -m u:input-x:rwx /usr/local/some-project

# Set default ACL for NEW files created in directory
sudo setfacl -d -m u:input-x:rwx /usr/local/some-project
```

## Viewing ACL Status

```bash
# Check ACL on specific file
getfacl /usr/local/bin/api-connect

# Check multiple files
getfacl /usr/local/bin/*

# See only ACL entries (not base permissions)
getfacl /usr/local | grep -v "^#"

# Check if file has ACL (+ sign in ls)
ls -l /usr/local/bin/api-connect
# -rwxr-xr-x+ 1 root root ... (+ means ACL is set)
```

## REMOVING Permissions

### Remove Specific ACL Entry

```bash
# Remove specific user's ACL
sudo setfacl -x u:input-x /usr/local/bin/api-connect

# Remove specific user from multiple files
sudo setfacl -x u:input-x /usr/local/bin/api-*
```

### Remove ALL ACLs (Reset to Base Permissions)

```bash
# Remove all ACLs from a file
sudo setfacl -b /usr/local/bin/api-connect

# Remove all ACLs from directory
sudo setfacl -b /usr/local

# Remove recursively (careful!)
sudo setfacl -R -b /usr/local/some-project
```

### Remove Default ACLs Only

```bash
# Remove default ACL (for new files) but keep existing ACLs
sudo setfacl -k /usr/local
```

## Common Scenarios

### Temporary Access Grant

```bash
# 1. Grant temporary access
sudo setfacl -m u:input-x:rwx /sensitive/file

# 2. Do the work...

# 3. Revoke access
sudo setfacl -x u:input-x /sensitive/file
```

### Project-Specific Access

```bash
# Create project area with full access
sudo mkdir /usr/local/aipass-dev
sudo setfacl -m u:input-x:rwx /usr/local/aipass-dev
sudo setfacl -d -m u:input-x:rwx /usr/local/aipass-dev  # Default for new files
```

### Read-Only Investigation

```bash
# Grant read access for debugging
sudo setfacl -m u:input-x:r-- /var/log/some-app.log

# Remove when done
sudo setfacl -x u:input-x /var/log/some-app.log
```

## Backup Recovery and Permission Reset

Restoring from the protected backup volume often copies files with the backup system's ACLs and ownership. Follow this workflow right after a restore so local services (like Drone) can write to their configs again.

### 1. Inspect the Restored Path
```bash
# Replace /path/to/restore with the directory you just recovered
ls -ld /path/to/restore
getfacl -R /path/to/restore | head
```
- Confirm the owner/group (should usually be `aipass:aipass` for workshop code).
- Look for ACL entries (`user:...` lines or the `+` on `ls -l`). These often block writes.

### 2. Reset Ownership and Unix Permissions
```bash
sudo chown -R aipass:aipass /path/to/restore
sudo chmod -R u+rwX,go+rX /path/to/restore
```
- `u+rwX` restores read/write for the owner, keeps execute only where it already existed.
- `go+rX` gives collaborators read + directory traversal without granting write.

### 3. Strip Backup ACLs (Most Common Fix)
```bash
sudo setfacl -R -b /path/to/restore
sudo setfacl -R -k /path/to/restore   # Optional: drop any default ACL templates
```
- `-b` removes all explicit ACL entries so only the base Unix bits apply.
- `-k` clears default ACLs that would apply to new files created later.

### 4. Validate Access
```bash
# Test that the application can write again
python3 - <<'PY'
from pathlib import Path
target = Path("/path/to/restore/some_file.json")
try:
    with target.open("r+", encoding="utf-8") as handle:
        content = handle.read()
        handle.seek(0)
        handle.write(content)
    print("write-ok")
except Exception as exc:
    print(f"error: {exc}")
PY
```
- Replace the path with the specific file that previously failed (for example `prax_logger_config.json`).
- Seeing `write-ok` confirms standard permissions are back in place.

### One-Line Reset (Use When in a Rush)
```bash
sudo chown -R aipass:aipass /path/to/restore && \
sudo chmod -R u+rwX,go+rX /path/to/restore && \
sudo setfacl -R -bk /path/to/restore
```
Run this immediately after copying from backup to bring ownership, chmod bits, and ACLs back to the workshop defaults.

## Security Considerations

### NEVER DO THIS
```bash
# DON'T grant recursive write to system directories
sudo setfacl -R -m u:input-x:rwx /usr  # DANGEROUS
sudo setfacl -R -m u:input-x:rwx /etc  # DANGEROUS
sudo setfacl -R -m u:input-x:rwx /     # SYSTEM KILLER
```

### SAFE PRACTICES
1. **Be Specific**: Target exact files/directories needed
2. **Avoid Recursive**: Unless absolutely necessary
3. **Document Changes**: Track what has ACLs and why
4. **Regular Audits**: Check for forgotten ACLs
5. **Minimum Required**: Only grant permissions actually needed

## Verification Commands

```bash
# Find all files with ACLs in a directory
find /usr/local -type f -exec getfacl {} \; 2>/dev/null | grep "user:input-x" -B1

# List all files with ACLs (+ in permissions)
ls -la /usr/local/bin | grep "+"

# Full ACL audit of directory
getfacl -R /usr/local 2>/dev/null | grep -E "^# file:|user:input-x"
```

## Current ACL Status in /usr/local

As of 2025-09-13:
- `/usr/local` - Directory creation rights (u:input-x:rwx)
- `/usr/local/bin/api-connect` - Full access (u:input-x:rwx)
- `/usr/local/bin/api-usage` - Full access (u:input-x:rwx)
- `/usr/local/bin/openrouter` - Full access (u:input-x:rwx)

## Quick Reference

| Task | Command |
|------|---------|
| Grant file access | `sudo setfacl -m u:input-x:rwx FILE` |
| Remove file access | `sudo setfacl -x u:input-x FILE` |
| Check ACL | `getfacl FILE` |
| Remove all ACLs | `sudo setfacl -b FILE` |
| Grant directory access | `sudo setfacl -m u:input-x:rwx DIR` |
| Set default for new files | `sudo setfacl -d -m u:input-x:rwx DIR` |
| Recursive grant (careful) | `sudo setfacl -R -m u:input-x:rwx DIR` |
| Find files with ACLs | `ls -la | grep "+"` |

## Troubleshooting

### Fixing "sudo: /etc/sudo.conf is group writable" Error

If you accidentally set recursive ACLs on /etc and sudo stops working:
```bash
# This breaks sudo because it detects insecure permissions
sudo setfacl -R -m u:username:rwx /etc  # DON'T DO THIS

# Fix: Remove ACLs from sudo configuration files
sudo setfacl -b /etc/sudo.conf
sudo setfacl -b /etc/sudoers
sudo setfacl -b -R /etc/sudoers.d/

# If sudo is completely broken, use su to become root first:
su -
setfacl -b /etc/sudo.conf
setfacl -b /etc/sudoers
exit
```

### Accidental Recursive ACL Removal

To remove accidentally applied recursive ACLs:
```bash
# Remove specific user's ACL recursively
sudo setfacl -R -x u:username /path/to/directory

# Remove ALL ACLs recursively (reset to base permissions)
sudo setfacl -R -b /path/to/directory

# Combination: remove all + remove defaults
sudo setfacl -Rbk /path/to/directory
```

## Emergency Cleanup

If something goes wrong:
```bash
# Remove ALL ACLs from /usr/local recursively
sudo setfacl -R -b /usr/local

# Restore standard permissions
sudo chmod 755 /usr/local
sudo chmod 755 /usr/local/bin
sudo chmod 755 /usr/local/bin/*
```

---
*This is critical system administration knowledge. Use with care and always verify changes.*
