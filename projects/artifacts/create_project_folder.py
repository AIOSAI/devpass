#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: create_project_folder.py
# Date: 2025-07-09
# Version: 0.3.0
# 
# CHANGELOG:
#   - v0.3.0 (2025-07-25): Removed README.md creation functionality
#   - v0.2.0 (2025-07-25): Added standardized metadata header structure
#   - v0.1.0 (2025-07-09): Universal project creation system with standardized structure
# =============================================

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# =============================================
# CONFIGURATION
# =============================================

DEFAULT_WORKSPACE = r"C:\AIPass-Ecosystem\flow\flow_workshop\claude_workspace\projects"
ENV_VAR = "CLAUDE_WORKSPACE_DIR"

# Universal folder structure for all projects
UNIVERSAL_FOLDERS = {
    "test_modules": "Workshop testing files for this project",
    "src": "Main project code and scripts", 
    "docs": "Documentation, notes, and guides",
    "resources": "Static assets, references, and examples",
    "archive": "Old versions and deprecated files"
}

# =============================================
# UTILITY FUNCTIONS
# =============================================

def get_workspace_dir():
    """Get the workspace directory from environment or use default."""
    path = os.environ.get(ENV_VAR)
    if path:
        workspace_dir = os.path.expanduser(path)
    else:
        workspace_dir = DEFAULT_WORKSPACE
    
    # STRICT VALIDATION: Ensure we're in the correct location
    expected_path = r"C:\AIPass-Ecosystem\flow\flow_workshop\claude_workspace\projects"
    if os.path.normpath(workspace_dir).lower() != os.path.normpath(expected_path).lower():
        print(f"ERROR: Workspace directory mismatch!")
        print(f"Expected: {expected_path}")
        print(f"Got: {workspace_dir}")
        sys.exit(1)
    
    # Only create if it doesn't exist AND it's the correct path
    if not os.path.exists(workspace_dir):
        os.makedirs(workspace_dir)
    
    return workspace_dir

def get_counter_file_path():
    """Get the path to the project counter JSON file."""
    workspace = get_workspace_dir()
    return os.path.join(os.path.dirname(workspace), "project_counter.json")

def load_project_counter():
    """Load the project counter from JSON file."""
    counter_file = get_counter_file_path()
    
    # Default counter structure
    default_counter = {
        "next_project_number": 1,
        "created_projects": [],
        "last_updated": datetime.now().isoformat()
    }
    
    try:
        if os.path.exists(counter_file):
            with open(counter_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Create the counter file if it doesn't exist
            save_project_counter(default_counter)
            return default_counter
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load project counter ({e}). Using default.")
        return default_counter

def save_project_counter(counter_data):
    """Save the project counter to JSON file."""
    counter_file = get_counter_file_path()
    counter_data["last_updated"] = datetime.now().isoformat()
    
    try:
        with open(counter_file, 'w', encoding='utf-8') as f:
            json.dump(counter_data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Warning: Could not save project counter ({e})")

def get_next_project_number():
    """Get the next project number and increment the counter."""
    counter = load_project_counter()
    current_number = counter["next_project_number"]
    counter["next_project_number"] = current_number + 1
    save_project_counter(counter)
    return current_number

def record_project_creation(project_number, title, folder_name, author):
    """Record a successfully created project in the counter."""
    counter = load_project_counter()
    
    project_record = {
        "number": project_number,
        "title": title,
        "folder_name": folder_name,
        "author": author,
        "created_date": datetime.now().isoformat(),
        "path": os.path.join(get_workspace_dir(), folder_name)
    }
    
    counter["created_projects"].append(project_record)
    save_project_counter(counter)

from typing import Optional
# Import flow_plan for PLAN creation
import sys
from pathlib import Path
# Add ecosystem root to path (5 levels up from projects/create_project_folder.py)
ecosystem_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ecosystem_root))
from aipass_core.flow.apps.flow_plan import create_plan

def sanitize_folder_name(name: Optional[str], project_number: Optional[int] = None) -> str:
    """Create a safe folder name from project title with optional numbering."""
    if name is None:
        name = "untitled"
    # Replace spaces and hyphens with underscores, handle dots and special chars
    clean = "".join(c if c.isalnum() or c in (" ", "_", "-", ".") else "_" for c in name)
    clean = clean.replace(" ", "_").replace("-", "_").replace(".", "_").lower()
    # Remove multiple underscores
    while "__" in clean:
        clean = clean.replace("__", "_")
    clean = clean.strip("_")
    
    # Add project number prefix if provided
    if project_number is not None:
        number_prefix = f"{project_number:04d}"
        return f"{number_prefix}_{clean}"
    return clean

# =============================================
# INPUT HELPERS
# =============================================

def normalize(cmd: str):
    """Strip leading ":", lowercase."""
    return cmd.lstrip(":").lower()

def prompt_input(prompt, default=None):
    """Single-line input with optional default."""
    if default is not None:
        prompt += f" [{default}]"
    
    try:
        raw = input(f"{prompt}: ").strip()
    except (KeyboardInterrupt, EOFError):
        return "cancel"
    
    norm = normalize(raw)
    if norm in ("back", "cancel", "quit", "exit"):
        return norm
    
    if not raw and default is not None:
        return default
    
    return raw

def collect_multiline_text(field_name, existing=None):
    """Read multi-line text, .END to finish."""
    if existing:
        print(f"Current {field_name}:")
        print("-" * 12)
        print(existing)
        print("-" * 12 + "\n")
    
    print(f"Enter {field_name} (end with a line containing only .END)")
    print("  (or type back/cancel to navigate)\n")
    
    lines = []
    while True:
        try:
            line = input()
        except (KeyboardInterrupt, EOFError):
            return "cancel", None
        
        norm = normalize(line.strip())
        if norm in ("back", "cancel"):
            return norm, None
        
        if line.strip().lower() == ".end":
            if existing and not lines:
                return "ok", existing
            return "ok", "\n".join(lines)
        
        lines.append(line)

# =============================================
# PROJECT CREATION
# =============================================

def create_project_folder(title, author, description):
    """Create the universal project folder structure."""
    # Get the next project number
    project_number = get_next_project_number()
    
    workspace = get_workspace_dir()
    folder_name = sanitize_folder_name(title, project_number)
    project_path = os.path.join(workspace, folder_name)
    
    # Check if folder already exists
    if os.path.exists(project_path):
        overwrite = prompt_input(f"Folder '{folder_name}' already exists. Overwrite? (y/n)", "n")
        if overwrite.lower() != "y":
            return None
        import shutil
        shutil.rmtree(project_path)
    
    # Create main project folder
    os.makedirs(project_path, exist_ok=True)
    
    # Create all universal folders
    for universal_folder, description in UNIVERSAL_FOLDERS.items():
        folder_path = os.path.join(project_path, universal_folder)
        os.makedirs(folder_path, exist_ok=True)
    
    # Record the successful project creation
    record_project_creation(project_number, title, folder_name, author)
    
    # Create a PLAN in the new project directory
    try:
        success, plan_num, plan_location, template_type, error_msg = create_plan(project_path, title)
    except Exception as e:
        print(f"Warning: Could not create PLAN: {e}")
        success = False
        plan_num = None
        plan_location = None
        template_type = None
        error_msg = str(e)
    if success:
        print(f"Created PLAN{plan_num:04d} in project folder")
    else:
        print(f"Warning: Could not create PLAN: {error_msg}")
    
    return project_path

# =============================================
# MAIN FLOW
# =============================================

def main():
    print("AIPass Universal Project Creator")
    print("===================================\n")
    
    step = 0
    author = None
    title = None
    description = None

    while True:
        # Step 0: Author
        if step == 0:
            ans = prompt_input("Author", default="InputX")
            if ans == "cancel":
                print("Aborted.")
                sys.exit(0)
            author = ans
            step = 1
            continue

        # Step 1: Project Title
        if step == 1:
            ans = prompt_input("Project Title", default=title)
            if ans == "cancel":
                print("Aborted.")
                sys.exit(0)
            if ans == "back":
                step = 0
                continue
            if not ans:
                continue
            title = ans
            step = 2
            continue

        # Step 2: Description
        if step == 2:
            status, text = collect_multiline_text("project description", existing=description)
            if status == "cancel":
                print("Aborted.")
                sys.exit(0)
            if status == "back":
                step = 1
                continue
            description = text
            step = 3
            continue

        # Step 3: Confirmation
        if step == 3:
            # Get the next project number for display (but don't increment yet)
            counter = load_project_counter()
            next_number = counter["next_project_number"]
            folder_name = sanitize_folder_name(title, next_number)
            print("\n" + "="*50)
            print("PROJECT SUMMARY")
            print("="*50)
            print(f"  Project #:   {next_number:04d}")
            print(f"  Title:       {title}")
            print(f"  Folder:      {folder_name}")
            print(f"  Author:      {author}")
            print(f"  Structure:   Universal (all project types)")
            print("\n  Description:")
            print("  " + "-"*47)
            print("  " + (description or "").replace("\n", "\n  "))
            print("  " + "-"*47)
            print()
            
            ans = prompt_input("Create project? (y/e/c)", "y")
            if ans.lower() == "y":
                try:
                    project_path = create_project_folder(title, author, description)
                    if project_path:
                        print(f"\nUniversal project created successfully!")
                        print(f"Location: {project_path}")
                        print(f"\nCreated folders:")
                        for folder in UNIVERSAL_FOLDERS.keys():
                            print(f"   - {folder}/")
                        print(f"\nNext steps:")
                        print(f"   1. Navigate to: {project_path}")
                        print(f"   2. Start building in the appropriate folders")
                        print(f"   3. Save chat logs in chat_history/ folder")
                        print(f"   4. Use test_modules/ for workshop testing")
                    sys.exit(0)
                except Exception as e:
                    print(f"Error creating project: {e}")
                    sys.exit(1)
            elif ans.lower() == "c":
                print("Aborted.")
                sys.exit(0)
            elif ans.lower() == "e":
                which = prompt_input("Edit what? (t=title, a=author, d=description)", "t")
                if which.lower() == "t":
                    step = 1
                elif which.lower() == "a":
                    step = 0
                elif which.lower() == "d":
                    step = 2
                continue

if __name__ == "__main__":
    main()
