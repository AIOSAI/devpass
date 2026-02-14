import os

# --- Folder mapping utilities ---

# Built-in ignore patterns. These are used if no external ignore file is
# provided. This keeps the ignore behavior self contained within this module
# as requested.
DEFAULT_IGNORE_PATTERNS = {
    '.git',
    '__pycache__',
    '.venv',
    'vendor',
    '*.pyc',
    '*.pyo',
    '.DS_Store',
    'node_modules',
    '*.log',
    '*.tmp',
    '*.swp',
    '*.bak',
    'lib',
}


def load_ignore_patterns(ignore_file=None):
    """Load ignore patterns from ``ignore_file`` if provided and merge them with
    the built in defaults.

    Parameters
    ----------
    ignore_file : str, optional
        Path to a file containing additional ignore patterns. If ``None`` or the
        file does not exist, only the default patterns are used.
    """
    patterns = set(DEFAULT_IGNORE_PATTERNS)
    if ignore_file and os.path.exists(ignore_file):
        with open(ignore_file, 'r') as f:
            patterns.update(
                line.strip()
                for line in f
                if line.strip() and not line.startswith('#')
            )
    return patterns

def should_ignore(name, ignore_patterns):
    for pattern in ignore_patterns:
        if pattern.startswith('*.') and name.endswith(pattern[1:]):
            return True
        if pattern == name or pattern in name:
            return True
    return False

def create_file_mapper_text(root_dir, output_file, ignore_file=None):
    """Create a text representation of `root_dir` including files."""
    ignore_patterns = load_ignore_patterns(ignore_file)
    with open(output_file, 'w') as file:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [d for d in dirnames if not should_ignore(d, ignore_patterns)]
            depth = dirpath.replace(root_dir, '').count(os.sep)
            indent = '|   ' * depth
            basename = os.path.basename(dirpath)
            if not should_ignore(basename, ignore_patterns):
                file.write(f"{indent}{basename}/\n")
                for fname in filenames:
                    if not should_ignore(fname, ignore_patterns):
                        file.write(f"{indent}|-- {fname}\n")

def list_project_files(root_dir=None, ignore_file=None):
    """Return a list of all files in the project, respecting ignore patterns."""
    if root_dir is None:
        root_dir = os.getcwd()
    ignore_patterns = load_ignore_patterns(ignore_file)
    file_list = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if not should_ignore(d, ignore_patterns)]
        for filename in filenames:
            if not should_ignore(filename, ignore_patterns):
                file_list.append(os.path.relpath(os.path.join(dirpath, filename), root_dir))
    return file_list

if __name__ == "__main__":
    root_directory = os.getcwd()  # Automatically get the current working directory
    output_filename = 'file_mapper.txt'  # Output file name
    create_file_mapper_text(root_directory, output_filename)

