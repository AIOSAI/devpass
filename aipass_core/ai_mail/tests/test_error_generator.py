#!/usr/bin/env python3
"""
Simple test script to generate errors for testing error_monitor deduplication.

Usage:
    python3 test_error_generator.py
"""

import logging
from pathlib import Path

# Setup logging to write to Flow logs directory (error_monitor watches this)
log_file = Path("/home/aipass/flow/logs/test_error_generator.log")
log_file.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("test_error_generator")

def main():
    """Generate a test error"""
    logger.error("Test error for deduplication testing - this should be caught by error_monitor")
    print(f"Test error generated - logged to {log_file}")
    print("Check AI_Mail inbox for notification")

if __name__ == "__main__":
    main()
