#!/usr/bin/env python3

# =============================================
# META DATA HEADER
# Name: flow_event_manager.py
# Date: 2025-08-28
# Version: 2.0.0
# Category: flow
# 
# CHANGELOG:
#   - v2.0.0 (2025-08-28): Cleaned obsolete handlers - removed flow_claude_status callbacks and auto-start
#   - v1.0.0 (2025-08-XX): Initial thread-safe event queuing system implementation
# =============================================

"""
AIPass Flow Event Manager
Thread-safe event queuing system for PLAN operations with deduplication

CURRENT STATUS: Clean foundation - no active handlers
- flow_claude_status.py removed in v1.0.0 production cleanup
- Callback systems eliminated per "APPROVED FOR PRODUCTION" audit
- Ready for future event handling needs

Following AIPass docs/standards/STANDARDS.md:
- 3-file JSON pattern (config, data, log)
- SystemLogger integration
- Error handling and recovery  
- Thread-safe operations
"""

import threading
import queue
import time
import json
import argparse
import sys
import os
from dataclasses import dataclass, asdict
from typing import List, Callable, Dict, Any
from pathlib import Path

# Path setup - standard pattern for all flow modules
AIPASS_ROOT = Path.home() / "aipass_core"
FLOW_ROOT = AIPASS_ROOT / "flow"
sys.path.append(str(AIPASS_ROOT))  # To ecosystem root

# Import system logger
from prax.apps.modules.prax_logger import system_logger as logger

# =============================================
# CONFIGURATION
# =============================================

# Module identity
MODULE_NAME = "flow_event_manager"

# System paths
ECOSYSTEM_ROOT = AIPASS_ROOT

@dataclass
class FlowEvent:
    event_type: str  # "plan_created", "plan_closed", "registry_changed" 
    plan_id: str
    timestamp: float
    data: Dict[str, Any]
    
    def to_dict(self):
        return asdict(self)

class FlowEventManager:
    def __init__(self):
        self.base_path = FLOW_ROOT / "flow_json"
        self.base_path.mkdir(exist_ok=True)
        
        # AIPass 3-file JSON pattern
        self.config_file = self.base_path / "flow_event_config.json"
        self.data_file = self.base_path / "flow_event_data.json" 
        self.log_file = self.base_path / "flow_event_log.json"
        
        # Thread management
        self.event_queue = queue.Queue()
        self.running = False
        self.worker_thread = None
        self.handlers: Dict[str, List[Callable]] = {}
        
        # Deduplication tracking
        self.recent_events = []
        self.dedupe_window = 2.0  # seconds
        
        # Logging  
        self.logger = logger
        
        # Initialize files
        self._load_config()
        self._load_data()
        self._load_log()
        
        self.logger.info("[FLOW_EVENT_MANAGER] Initialized")
    
    def _load_config(self):
        """Load configuration settings"""
        default_config = {
            "version": "1.0.0",
            "dedupe_window_seconds": 2.0,
            "max_queue_size": 1000,
            "worker_timeout": 1.0,
            "enabled_event_types": [
                "plan_created",
                "plan_closed", 
                "plan_moved",
                "registry_changed"
            ]
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in default_config.items():
                    if key not in self.config:
                        self.config[key] = value
            except Exception as e:
                self.logger.error(f"Config load failed: {e}")
                self.config = default_config
        else:
            self.config = default_config
            
        # Update instance settings
        self.dedupe_window = self.config.get("dedupe_window_seconds", 2.0)
        
        # Save config
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Config save failed: {e}")
    
    def _load_data(self):
        """Load runtime data"""
        default_data = {
            "total_events_processed": 0,
            "events_by_type": {},
            "last_event_timestamp": 0,
            "handler_count": 0
        }

        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except Exception as e:
                self.logger.error(f"Data load failed: {e}")
                self.data = default_data
        else:
            self.data = default_data
            # Create initial data file
            try:
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, indent=2)
            except Exception as e:
                self.logger.error(f"Data file creation failed: {e}")
    
    def _load_log(self):
        """Load operation logs"""
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    self.operation_log = json.load(f)
            except Exception as e:
                self.logger.error(f"Log load failed: {e}")
                self.operation_log = []
        else:
            self.operation_log = []
            # Create initial log file
            try:
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    json.dump(self.operation_log, f, indent=2)
            except Exception as e:
                self.logger.error(f"Log file creation failed: {e}")
    
    def _save_data(self):
        """Save runtime data"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Data save failed: {e}")
    
    def _log_operation(self, operation: str, success: bool, details: str, error: str = ""):
        """Log operation to JSON file"""
        entry = {
            "timestamp": time.time(),
            "operation": operation,
            "success": success,
            "details": details,
            "error": error
        }
        
        self.operation_log.append(entry)
        
        # Keep only last 1000 entries
        if len(self.operation_log) > 1000:
            self.operation_log = self.operation_log[-1000:]
        
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.operation_log, f, indent=2)
        except Exception as e:
            self.logger.error(f"Log save failed: {e}")
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register event handler"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append(handler)
        self.data["handler_count"] = sum(len(handlers) for handlers in self.handlers.values())
        self._save_data()
        
        self.logger.info(f"Registered handler for {event_type} (total: {self.data['handler_count']})")
        self._log_operation("register_handler", True, f"Handler registered for {event_type}")
    
    def queue_event(self, event: FlowEvent):
        """Queue event for processing"""
        if not self.running:
            self.logger.warning("Event manager not running - starting automatically")
            self.start()
        
        # Check if event type is enabled
        if event.event_type not in self.config.get("enabled_event_types", []):
            self.logger.info(f"Skipping disabled event type: {event.event_type}")
            return
        
        try:
            self.event_queue.put(event, timeout=1.0)
            self.logger.info(f"Queued event: {event.event_type} for {event.plan_id}")
            self._log_operation("queue_event", True, f"Queued {event.event_type} for {event.plan_id}")
        except queue.Full:
            self.logger.error("Event queue full - dropping event")
            self._log_operation("queue_event", False, f"Queue full for {event.event_type}", "Queue at capacity")
    
    def _is_duplicate_event(self, event: FlowEvent) -> bool:
        """Check if this is a duplicate recent event"""
        now = time.time()
        
        # Clean old events
        self.recent_events = [e for e in self.recent_events 
                            if now - e.timestamp < self.dedupe_window]
        
        # Check for duplicates
        for recent in self.recent_events:
            if (recent.event_type == event.event_type and 
                recent.plan_id == event.plan_id):
                return True
        
        return False
    
    def process_events(self):
        """Main event processing loop (runs in worker thread)"""
        self.logger.info("[FLOW_EVENT_MANAGER] Worker thread started")
        
        while self.running:
            try:
                event = self.event_queue.get(timeout=self.config.get("worker_timeout", 1.0))
                
                # Check for duplicates
                if self._is_duplicate_event(event):
                    self.logger.info(f"Skipping duplicate {event.event_type} for {event.plan_id}")
                    self._log_operation("process_event", True, f"Skipped duplicate {event.event_type} for {event.plan_id}")
                    continue
                
                # Add to recent events for deduplication
                self.recent_events.append(event)
                
                # Process event handlers
                if event.event_type in self.handlers:
                    for i, handler in enumerate(self.handlers[event.event_type]):
                        try:
                            self.logger.info(f"Processing {event.event_type} with handler {i+1}")
                            handler(event)
                            self._log_operation("process_handler", True, 
                                              f"Handler {i+1} processed {event.event_type} for {event.plan_id}")
                        except Exception as e:
                            self.logger.error(f"Handler {i+1} error: {e}")
                            self._log_operation("process_handler", False, 
                                              f"Handler {i+1} failed for {event.event_type}", str(e))
                else:
                    self.logger.warning(f"No handlers for event type: {event.event_type}")
                
                # Update statistics
                self.data["total_events_processed"] += 1
                if event.event_type not in self.data["events_by_type"]:
                    self.data["events_by_type"][event.event_type] = 0
                self.data["events_by_type"][event.event_type] += 1
                self.data["last_event_timestamp"] = event.timestamp
                self._save_data()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Event processing error: {e}")
                self._log_operation("process_event", False, "Event processing failed", str(e))
    
    def start(self):
        """Start the event manager"""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self.process_events, name="FlowEventManager")
            self.worker_thread.daemon = True
            self.worker_thread.start()
            
            self.logger.info("[FLOW_EVENT_MANAGER] Started worker thread")
            self._log_operation("start", True, "Event manager started")
    
    def stop(self):
        """Stop the event manager"""
        if self.running:
            self.running = False
            if self.worker_thread:
                self.worker_thread.join(timeout=5.0)
            
            self.logger.info("[FLOW_EVENT_MANAGER] Stopped")
            self._log_operation("stop", True, "Event manager stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        return {
            "running": self.running,
            "queue_size": self.event_queue.qsize(),
            "handler_count": self.data["handler_count"],
            "total_processed": self.data["total_events_processed"],
            "events_by_type": self.data["events_by_type"],
            "recent_events_count": len(self.recent_events)
        }

# Global instance (no auto-start - handlers must be explicitly registered)
event_manager = FlowEventManager()

def handle_status(args):
    """Handle status command"""
    stats = event_manager.get_stats()
    print("\n=== Flow Event Manager Status ===")
    print(f"Running: {stats['running']}")
    print(f"Queue Size: {stats['queue_size']}")
    print(f"Handler Count: {stats['handler_count']}")
    print(f"Total Processed: {stats['total_processed']}")
    print(f"Recent Events: {stats['recent_events_count']}")
    print(f"Events by Type: {stats['events_by_type']}")
    print("=" * 32)

def handle_start(args):
    """Handle start command"""
    if event_manager.running:
        print("Event manager is already running")
    else:
        event_manager.start()
        print("Event manager started")

def handle_stop(args):
    """Handle stop command"""
    if not event_manager.running:
        print("Event manager is not running")
    else:
        event_manager.stop()
        print("Event manager stopped")

def handle_stats(args):
    """Handle stats command"""
    stats = event_manager.get_stats()
    print(json.dumps(stats, indent=2))

def handle_config(args):
    """Handle config command"""
    print(json.dumps(event_manager.config, indent=2))

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='AIPass Flow Event Manager - Thread-safe event queuing system for PLAN operations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMMANDS:
  Commands: status, start, stop, stats, config

  status - Show current event manager status
  start  - Start the event manager
  stop   - Stop the event manager
  stats  - Display event statistics in JSON format
  config - Display configuration settings in JSON format

EXAMPLES:
  python3 flow_event_manager.py status
  python3 flow_event_manager.py start
  python3 flow_event_manager.py stop
  python3 flow_event_manager.py stats
  python3 flow_event_manager.py config
        """
    )

    parser.add_argument('command',
                       choices=['status', 'start', 'stop', 'stats', 'config'],
                       nargs='?',
                       default='status',
                       help='Command to execute')

    args = parser.parse_args()

    if args.command == 'status':
        handle_status(args)
    elif args.command == 'start':
        handle_start(args)
    elif args.command == 'stop':
        handle_stop(args)
    elif args.command == 'stats':
        handle_stats(args)
    elif args.command == 'config':
        handle_config(args)

    return 0

# Module info
if __name__ == "__main__":
    sys.exit(main())