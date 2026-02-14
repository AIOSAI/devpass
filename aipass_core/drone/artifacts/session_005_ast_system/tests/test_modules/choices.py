#!/usr/bin/env python3
"""
Test Module: Choices Pattern
Pattern: Choices pattern (like backup_cli.py)
"""

import argparse
import sys

def main():
    parser = argparse.ArgumentParser(
        description='Test module with choices pattern'
    )

    parser.add_argument(
        'mode',
        nargs='?',
        choices=['snapshot', 'versioned', 'incremental'],
        help='Backup mode to use'
    )

    parser.add_argument(
        '--note',
        type=str,
        help='Note for the operation'
    )

    parser.add_argument(
        '--list-modes',
        action='store_true',
        help='List available backup modes'
    )

    args = parser.parse_args()

    if args.list_modes:
        print("Available modes: snapshot, versioned, incremental")
        sys.exit(0)

    if not args.mode:
        parser.print_help()
        sys.exit(1)

    print(f"Executing mode: {args.mode}")
    if args.note:
        print(f"Note: {args.note}")

if __name__ == '__main__':
    main()
