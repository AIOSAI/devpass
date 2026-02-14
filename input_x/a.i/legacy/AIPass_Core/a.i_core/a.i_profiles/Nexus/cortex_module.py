# cortex_module.py — Self-contained Cortex system for AI assistant awareness

import os
import json
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
from llm_client import chat, make_client
from config_loader import load_api_config

# === CONFIG ===
VALID_EXTENSIONS = {".py", ".json", ".md", ".txt"}
SKIP_FILES = {
    "chat_history.json",
    "previous_chat_summaries.json",
    "live_memory.json",
    "file_cache.json",
    "pulse_counter.json",
    "cortex.json",
    "profile.json"
}
CORTEX_PATH = Path(__file__).with_name("cortex.json")

# === File watcher for auto-updates ===
class CortexFileWatcher(FileSystemEventHandler):
    def on_any_event(self, event):
        pass  # Event logging removed for production
    
    def on_created(self, event):
        if not event.is_directory and self._is_valid_file(event.src_path):
            file_path = Path(event.src_path)
            print(f"[Cortex] New file detected: {file_path.name}")
            try:
                self._update_file_with_change(file_path, "created")
                print(f"[Cortex] Successfully updated cortex.json")
            except Exception as e:
                print(f"[Cortex] ERROR updating cortex: {e}")
    
    def on_modified(self, event):
        if not event.is_directory and self._is_valid_file(event.src_path):
            file_path = Path(event.src_path)
            print(f"[Cortex] File modified: {file_path.name}")
            try:
                self._update_file_with_change(file_path, "modified")
                print(f"[Cortex] Successfully updated cortex.json")
            except Exception as e:
                print(f"[Cortex] ERROR updating cortex: {e}")
    
    def on_deleted(self, event):
        if not event.is_directory and self._is_valid_file(event.src_path):
            file_path = Path(event.src_path)
            print(f"[Cortex] File deleted: {file_path.name}")
            try:
                self._update_file_with_change(file_path, "deleted")
                print(f"[Cortex] Successfully updated cortex.json after deletion")
            except Exception as e:
                print(f"[Cortex] ERROR updating cortex after deletion: {e}")
    
    def _is_valid_file(self, file_path):
        path = Path(file_path)
        
        result = (path.suffix.lower() in VALID_EXTENSIONS and 
                  path.name not in SKIP_FILES and
                  path.name != "cortex.json")
        print(f"[DEBUG] Valid file result: {result}")
        return result
    
    def _update_file_with_change(self, file_path, change_type):
        """Update cortex.json with file change information"""
        cortex = load_cortex()
        base_dir = Path(__file__).parent
        rel_path = str(file_path.relative_to(base_dir))
        timestamp = datetime.now().isoformat()
        
        if change_type == "deleted":
            # For deleted files, mark as deleted but keep entry for awareness
            if rel_path in cortex:
                cortex[rel_path]["last_change_type"] = "deleted"
                cortex[rel_path]["last_change_time"] = timestamp
                cortex[rel_path]["file_exists"] = False
                # Increment change counter
                cortex[rel_path]["changes_this_session"] = cortex[rel_path].get("changes_this_session", 0) + 1
        else:
            # For created/modified files, do full refresh and add change tracking
            if file_path.exists():
                mtime = file_path.stat().st_mtime
                
                # Generate summary if file is new or changed
                try:
                    content = file_path.read_text(encoding="utf-8")
                    summary = self._generate_summary(content)
                except Exception as e:
                    summary = f"[Failed to summarize: {e}]"
                
                # Update or create cortex entry with change tracking
                if rel_path not in cortex:
                    cortex[rel_path] = {"changes_this_session": 0}
                
                cortex[rel_path].update({
                    "summary": summary,
                    "mtime": mtime,
                    "last_change_type": change_type,
                    "last_change_time": timestamp,
                    "file_exists": True,
                    "changes_this_session": cortex[rel_path].get("changes_this_session", 0) + 1
                })
        
        # Save updated cortex
        CORTEX_PATH.write_text(json.dumps(cortex, ensure_ascii=False, indent=2), encoding="utf-8")
    
    def _generate_summary(self, content):
        """Generate summary for file content"""
        try:
            # Load config and initialize LLM client
            cfg = load_api_config()
            active = [p for p, v in cfg["providers"].items() if v.get("enabled")][0]
            
            # Get API key from API manager
            try:
                from api_manager.api_manager import get_api_manager
                api_mgr = get_api_manager()
                api_key = api_mgr.get_key(active)
            except Exception as e:
                raise ValueError(f"No API key found for {active} in API manager: {e}")
            
            client = make_client(active, api_key)
            model = cfg["providers"][active]["model"]
            temp = cfg["providers"][active].get("temperature", 0.3)
            
            prompt = [
                {"role": "system", "content": "Summarize the following file in 1–2 sentences. Focus on purpose and key logic."},
                {"role": "user", "content": content}
            ]
            summary = chat(active, client, model, prompt, temp)
            return " ".join(summary.strip().split()[:15])  # keep it short
        except Exception as e:
            return f"[Failed to summarize: {e}]"

# === Load or initialize cortex ===
def load_cortex():
    if CORTEX_PATH.exists():
        try:
            return json.loads(CORTEX_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {}

# === Scan and summarize ===
def refresh_cortex_summary():
    cortex = load_cortex()
    base_dir = Path(__file__).parent
    current_files = {}

    for root, _, files in os.walk(base_dir):
        for fname in files:
            path = Path(root) / fname
            rel_path = path.relative_to(base_dir)
            if path.suffix.lower() in VALID_EXTENSIONS and path.name not in SKIP_FILES:
                mtime = path.stat().st_mtime
                current_files[str(rel_path)] = {"path": path, "mtime": mtime}

    to_update = [f for f in current_files if f not in cortex or cortex[f]["mtime"] != current_files[f]["mtime"]]
    to_delete = [f for f in cortex if f not in current_files]

    # Load config and initialize LLM client
    cfg = load_api_config()
    active = [p for p, v in cfg["providers"].items() if v.get("enabled")][0]
    # Get API key from API manager (like nexus.py does)
    try:
        from api_manager.api_manager import get_api_manager
        api_mgr = get_api_manager()
        api_key = api_mgr.get_key(active)
    except Exception as e:
        raise ValueError(f"No API key found for {active} in API manager: {e}")
    
    client = make_client(active, api_key)
    model = cfg["providers"][active]["model"]
    temp = cfg["providers"][active].get("temperature", 0.3)
    
    for rel_path in to_update:
        file_path = current_files[rel_path]["path"]
        try:
            content = file_path.read_text(encoding="utf-8")
            prompt = [
                {"role": "system", "content": "Summarize the following file in 1–2 sentences. Focus on purpose and key logic."},
                {"role": "user", "content": content}
            ]
            summary = chat(active, client, model, prompt, temp)
            summary = " ".join(summary.strip().split()[:30])  # keep it short
            
            # Preserve existing change tracking data if it exists
            if rel_path not in cortex:
                cortex[rel_path] = {}
            
            cortex[rel_path].update({
                "summary": summary,
                "mtime": current_files[rel_path]["mtime"],
                "file_exists": True
            })
            
            # Initialize change tracking fields if they don't exist
            if "changes_this_session" not in cortex[rel_path]:
                cortex[rel_path]["changes_this_session"] = 0
            if "last_change_type" not in cortex[rel_path]:
                cortex[rel_path]["last_change_type"] = "existing"
            if "last_change_time" not in cortex[rel_path]:
                cortex[rel_path]["last_change_time"] = datetime.now().isoformat()
                
        except Exception as e:
            if rel_path not in cortex:
                cortex[rel_path] = {}
            cortex[rel_path].update({
                "summary": f"[Failed to summarize: {e}]",
                "mtime": current_files[rel_path]["mtime"],
                "file_exists": True,
                "changes_this_session": cortex[rel_path].get("changes_this_session", 0),
                "last_change_type": "existing",
                "last_change_time": datetime.now().isoformat()
            })

    # Mark deleted files
    for f in to_delete:
        cortex[f]["file_exists"] = False
        cortex[f]["last_change_type"] = "deleted"
        cortex[f]["last_change_time"] = datetime.now().isoformat()

    CORTEX_PATH.write_text(json.dumps(cortex, ensure_ascii=False, indent=2), encoding="utf-8")
    return cortex

# === Prompt block for awareness ===
def get_cortex_summary_block():
    cortex = load_cortex()
    lines = ["## SYSTEM FILE MAP (via Cortex)"]
    for file, meta in sorted(cortex.items()):
        summary = meta.get("summary", "").strip()
        last_change = meta.get("last_change_type", "unknown")
        change_time = meta.get("last_change_time", "unknown")
        changes_count = meta.get("changes_this_session", 0)
        file_exists = meta.get("file_exists", True)
        
        # Format change information for Nexus awareness
        change_info = ""
        if last_change != "existing":
            if change_time != "unknown":
                try:
                    # Parse the timestamp and make it readable
                    dt = datetime.fromisoformat(change_time.replace('Z', '+00:00'))
                    time_str = dt.strftime("%H:%M:%S")
                    change_info = f" [{last_change} at {time_str}"
                    if changes_count > 1:
                        change_info += f", {changes_count} changes this session"
                    change_info += "]"
                except:
                    change_info = f" [{last_change}]"
        
        status_indicator = "" if file_exists else " [DELETED]"
        lines.append(f"- {file}{status_indicator} -> {summary}{change_info}")
    
    return "\n".join(lines)

# === Watcher control functions ===
_observer = None

def start_cortex_watcher():
    """Start the filesystem watcher for auto-updates."""
    global _observer
    if _observer and _observer.is_alive():
        return  # Already running
    
    base_dir = Path(__file__).parent
    _observer = Observer()
    _observer.schedule(CortexFileWatcher(), str(base_dir), recursive=True)
    _observer.start()
    print(f"[Cortex] Filesystem watcher started for {base_dir}")

def stop_cortex_watcher():
    """Stop the filesystem watcher."""
    global _observer
    if _observer and _observer.is_alive():
        _observer.stop()
        _observer.join()
        print("[Cortex] Filesystem watcher stopped")

# === Session management ===
def reset_session_counters():
    """Reset changes_this_session for all files when new chat starts"""
    cortex = load_cortex()
    session_reset_count = 0
    
    for rel_path, file_entry in cortex.items():
        # Reset session counter
        if file_entry.get("changes_this_session", 0) > 0:
            session_reset_count += 1
        file_entry["changes_this_session"] = 0
        
        # Initialize missing change tracking fields for existing entries
        if "last_change_type" not in file_entry:
            file_entry["last_change_type"] = "existing"
        if "last_change_time" not in file_entry:
            file_entry["last_change_time"] = datetime.now().isoformat()
        if "file_exists" not in file_entry:
            file_entry["file_exists"] = True
    
    # Save updated cortex
    CORTEX_PATH.write_text(json.dumps(cortex, ensure_ascii=False, indent=2), encoding="utf-8")
    
    if session_reset_count > 0:
        print(f"[Cortex] Session reset: cleared change counters for {session_reset_count} files")
    else:
        print(f"[Cortex] Session initialized: {len(cortex)} files tracked")

# === Runtime use ===
if __name__ == "__main__":
    import sys
    
    updated = refresh_cortex_summary()
    print(f"Updated {len(updated)} file summaries.")
    sys.stdout.flush()
    
    # Start the watcher
    start_cortex_watcher()
    
    # Keep running
    try:
        print("Press Ctrl+C to stop watching...")
        sys.stdout.flush()
        counter = 0
        while True:
            import time
            time.sleep(1)
            counter += 1
            if counter % 10 == 0:  # Print every 10 seconds
                print(f"[DEBUG] Watcher still running... ({counter}s)")
                sys.stdout.flush()
    except KeyboardInterrupt:
        stop_cortex_watcher()
        print("Cortex watcher stopped.")
        sys.stdout.flush()