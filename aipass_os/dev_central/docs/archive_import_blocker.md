# Archive Import Blocker

Python import blocker that prevents code execution from archive/backup directories.

## Purpose

Prevents accidental imports from inactive storage directories. These directories contain old code, backups, and deleted content that should never be executed.

## Blocked Directories

- `.archive` - Branch-level archived code
- `code_archive` - Memory Bank code archive
- `backups` - Backup system storage
- `.backup` - Branch backup snapshots
- `pruned_files` - Backup system pruned files
- `deleted_branches` - Backup system deleted branches
- `dropbox` - File dropbox (various branches)
- `downloads` - Download directories

## How It Works

Two files in the venv's site-packages:

| File | Purpose |
|------|---------|
| `archive_blocker.pth` | Triggers blocker on Python startup |
| `_archive_blocker.py` | The actual blocker implementation |

**Location**: `/home/aipass/.venv/lib/python3.14/site-packages/`

### Mechanism

1. `.pth` files are processed by Python on startup
2. `archive_blocker.pth` imports `_archive_blocker`
3. The blocker:
   - Filters `sys.path` to remove blocked directories
   - Installs a `MetaPathFinder` that blocks imports from blocked paths
   - Raises `ModuleNotFoundError` with "BLOCKED:" prefix if import attempted

## Testing

```bash
# Check if blocker is active
python3 -c "import sys; print('Active:', any('ArchiveBlocker' in str(type(f)) for f in sys.meta_path))"

# Test blocking (should fail with BLOCKED error)
python3 -c "
import sys
sys.path.insert(0, '/home/aipass/MEMORY_BANK/code_archive')
import some_module  # Will raise: BLOCKED: some_module
"
```

## Why .pth File?

- `sitecustomize.py` in venv is ignored (system one takes precedence)
- `usercustomize.py` requires `ENABLE_USER_SITE=True` (disabled in venv)
- `.pth` files ARE processed from venv site-packages

## Adding New Blocked Directories

Edit `/home/aipass/.venv/lib/python3.14/site-packages/_archive_blocker.py`:

```python
BLOCKED_DIRS = [
    '.archive', 'code_archive', 'backups', '.backup',
    'pruned_files', 'deleted_branches', 'dropbox', 'downloads',
    'new_blocked_dir',  # Add here
]
```

## Limitations

- Only blocks Python imports, not direct file execution (`python /path/file.py`)
- Only applies to processes using the venv
- Code can still be read/copied from blocked directories

---

*Created: 2025-12-04*
*Session: 38*
