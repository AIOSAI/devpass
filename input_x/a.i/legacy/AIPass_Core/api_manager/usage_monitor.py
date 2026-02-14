# --- Token Usage Monitor ---

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# --- Path resolution ---
# Ensure we can find the module regardless of how it's imported
root = Path(__file__).resolve()
while root.name != "AIPass_Core" and root != root.parent:
    root = root.parent

core_dir = root
repo_root = core_dir.parent

# Add paths to sys.path if not already present
for p in (str(repo_root), str(core_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

class UsageMonitor:
    def __init__(self, log_file_path=None):
        """Initialize the usage monitor with JSON log file"""
        if log_file_path is None:
            # Store in the same directory as this file
            log_file_path = Path(__file__).parent / "usage_log.json"
        
        self.log_file_path = Path(log_file_path)
        self.max_entries = 20
        
        # Create empty log if it doesn't exist
        if not self.log_file_path.exists():
            self._save_log([])
    
    def log_usage(self, provider, model, input_tokens, output_tokens):
        """Log token usage for a single API call"""
        # Load existing log
        log_data = self._load_log()
        
        # Create new entry
        entry = {
            "timestamp": datetime.now().isoformat(),
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens
        }
        
        # Add to beginning of list (newest first)
        log_data.insert(0, entry)
        
        # Keep only max entries
        if len(log_data) > self.max_entries:
            log_data = log_data[:self.max_entries]
        
        # Save back to file
        self._save_log(log_data)
    
    def get_recent_usage(self):
        """Get the recent usage log"""
        return self._load_log()
    
    def clear_log(self):
        """Clear the usage log"""
        self._save_log([])
    
    def _load_log(self):
        """Load the log from JSON file"""
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_log(self, log_data):
        """Save the log to JSON file and flush to disk immediately"""
        # First write to a temporary file, then rename it to the target file
        # This approach avoids issues with file locking
        temp_path = self.log_file_path.with_suffix('.tmp')
        try:
            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            
            # Replace the original file with the temp file
            # This is an atomic operation on most file systems
            temp_path.replace(self.log_file_path)
            
            
        except Exception as e:
            
            # If the temp approach fails, try direct write as fallback
            with open(self.log_file_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())

# Singleton instance
_usage_monitor = None

def get_usage_monitor():
    """Get the singleton usage monitor instance"""
    global _usage_monitor
    if _usage_monitor is None:
        _usage_monitor = UsageMonitor()
    return _usage_monitor
