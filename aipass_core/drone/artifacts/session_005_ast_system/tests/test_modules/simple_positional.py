#!/usr/bin/env python3
"""
Test Module: Simple Positional Arguments
Pattern: Basic positional argument with choices
"""

import argparse
import sys

def main():
    parser = argparse.ArgumentParser(
        description='Simple test module with positional argument'
    )

    parser.add_argument(
        'command',
        choices=['start', 'stop', 'restart'],
        help='Command to execute'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    print(f"Executing: {args.command}")
    if args.verbose:
        print("Verbose mode enabled")

if __name__ == '__main__':
    main()
