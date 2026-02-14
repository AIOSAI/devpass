#!/usr/bin/env python3
"""Performance monitoring operations for drone"""
import subprocess
import sys

def monitor_pylance(args):
    """Monitor Pylance memory usage

    Usage:
        drone @perf monitor          - Basic memory check
        drone @perf monitor --files  - Include Python file count
    """
    cmd = ["pylance-monitor"]
    if "--files" in args or "-f" in args:
        cmd.append("--files")

    result = subprocess.run(cmd)
    return result.returncode

def main():
    """Main entry point for perf operations"""
    if len(sys.argv) < 2:
        return 0

    command = sys.argv[1]

    if command == "monitor":
        return monitor_pylance(sys.argv[2:])
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
