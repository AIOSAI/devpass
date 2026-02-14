# --- Token Usage Monitor ---

import os
import sys
import json
from datetime import datetime
import inspect
from pathlib import Path
from typing import Dict, List, Any
import file_mapper

# --- Path resolution ---
# Ensure we can find the module regardless of how it's imported
ROOT_PATH = Path(__file__).resolve().parent.parent

ENABLED = True

def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    """Count tokens in text using simple approximation"""
    if not text:
        return 0
    
    # Simple approximation: ~4 characters per token for most text
    # This is reasonably accurate for English text
    char_count = len(text)
    estimated_tokens = max(1, char_count // 4)
    
    # Add small adjustment for common patterns
    # Whitespace and punctuation tend to be more token-dense
    whitespace_count = text.count(' ') + text.count('\n') + text.count('\t')
    estimated_tokens += whitespace_count // 8
    
    return estimated_tokens

def analyze_prompt_contributions(
    system_prompt: str = None,
    session_context: str = None,
    cache_content: str = "",
    user_input: str = "",
    context_messages: List[Dict[str, str]] = None,
    model: str = "gpt-4o-mini",
    **kwargs
) -> Dict[str, Any]:
    """Analyze token contribution from each prompt source
    
    This function dynamically analyzes all prompt components and session context.
    It accepts any number of prompt components via kwargs and tracks them all.
    
    Args:
        system_prompt: The full system prompt (optional)
        session_context: The session context string (optional)
        cache_content: Content from file cache
        user_input: The user's input
        context_messages: List of context messages
        model: The model name for token counting
        **kwargs: Any additional prompt components to track
    """
    
    if context_messages is None:
        context_messages = []
    
    # Initialize breakdown with dynamic prompt sources
    breakdown = {
        "prompt_sources": {},
        "session_context": count_tokens(session_context or "", model),
        "cache_content": count_tokens(cache_content, model),
        "user_input": count_tokens(user_input, model),
        "context_history": 0,
        "total_estimated": 0
    }
    
    # Add system prompt if provided
    if system_prompt:
        breakdown["system_prompt"] = count_tokens(system_prompt, model)
    
    # Add all additional prompt components from kwargs
    for key, value in kwargs.items():
        if isinstance(value, str):
            breakdown["prompt_sources"][key] = count_tokens(value, model)
    
    # Count context history tokens
    for msg in context_messages:
        breakdown["context_history"] += count_tokens(msg.get("content", ""), model)
    
    # Calculate total
    prompt_sources_total = sum(breakdown["prompt_sources"].values()) if breakdown["prompt_sources"] else 0
    breakdown["total_estimated"] = (
        prompt_sources_total +
        breakdown.get("system_prompt", 0) +
        breakdown["session_context"] +
        breakdown["cache_content"] +
        breakdown["user_input"] +
        breakdown["context_history"]
    )
    
    return breakdown

class UsageMonitor:
    def __init__(self, log_file_path=None):
        """Initialize the usage monitor with JSON log file"""
        if log_file_path is None:
            # Store in the same directory as this file
            log_file_path = Path(__file__).parent / "usage_log.json"
        print(f"[UsageMonitor] Initializing with log file: {log_file_path}")
        self.log_file_path = Path(log_file_path)
        self.max_entries = 20
        
        # Create empty log if it doesn't exist
        if not self.log_file_path.exists():
            print(f"[UsageMonitor] Log file does not exist. Creating: {self.log_file_path}")
            self._save_log([])
    
    def log_usage(self, provider, model, input_tokens, output_tokens, system=None, breakdown=None, token_contributions=None):
        print(f"[UsageMonitor] Logging usage: provider={provider}, model={model}, input_tokens={input_tokens}, output_tokens={output_tokens}, system={system}")
        if system is None:
            stack = inspect.stack()
            for frame in stack[1:]:
                try:
                    path = Path(frame.filename).resolve()
                    if ROOT_PATH in path.parents and path.suffix == ".py":
                        system = path.stem  # e.g., "main", "file_create"
                        break
                except Exception:
                    continue
            else:
                system = "unknown"

        entry = {
            "timestamp": datetime.now().isoformat(),
            "system": system,
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens
        }
        
        # Add file-level breakdown if provided
        if breakdown is not None:
            entry["breakdown"] = breakdown
        
        # Add detailed token contributions if provided
        if token_contributions is not None:
            entry["token_contributions"] = token_contributions

        log_data = self._load_log()
        log_data.insert(0, entry)
        if len(log_data) > self.max_entries:
            log_data = log_data[:self.max_entries]
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
        
        temp_path = self.log_file_path.with_suffix('.tmp')
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            temp_path.replace(self.log_file_path)
            
        except Exception as e:
            print(f"[UsageMonitor] Error saving log: {e}")
            with open(self.log_file_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())

# Singleton instance
_usage_monitor = None

def get_usage_monitor():
    """
    Get the singleton usage monitor instance.
    Returns:
        UsageMonitor: The singleton usage monitor.
    """
    global _usage_monitor
    if _usage_monitor is None:
        _usage_monitor = UsageMonitor()
    return _usage_monitor

if __name__ == "__main__":
    print("[UsageMonitor] Running test log entry...")
    get_usage_monitor().log_usage(
        provider="test_provider",
        model="test_model",
        input_tokens=123,
        output_tokens=45
    )
    print("[UsageMonitor] Test log entry complete. Check for usage_log.json in the same directory as this file.")
