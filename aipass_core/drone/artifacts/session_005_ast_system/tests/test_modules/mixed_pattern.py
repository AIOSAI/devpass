#!/usr/bin/env python3
"""
Test Module: Mixed Pattern
Pattern: Combination of positional, choices, and flags
"""

import argparse
import sys

def main():
    parser = argparse.ArgumentParser(
        description='Test module with mixed patterns'
    )

    # Positional with choices
    parser.add_argument(
        'action',
        choices=['build', 'test', 'deploy', 'rollback'],
        help='Action to perform'
    )

    # Optional positional
    parser.add_argument(
        'target',
        nargs='?',
        default='default',
        help='Target environment'
    )

    # Optional flags
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--config',
        type=str,
        help='Path to config file'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform a dry run'
    )

    args = parser.parse_args()

    print(f"Action: {args.action}")
    print(f"Target: {args.target}")
    if args.verbose:
        print("Verbose: enabled")
    if args.config:
        print(f"Config: {args.config}")
    if args.dry_run:
        print("Dry run mode")

if __name__ == '__main__':
    main()
