#!/usr/bin/env python3
"""
Test Module: Subparsers Pattern
Pattern: Standard subparser pattern (like flow_plan.py)
"""

import argparse
import sys

def main():
    parser = argparse.ArgumentParser(
        description='Test module with subparsers'
    )

    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands'
    )

    # Create subcommand
    create_parser = subparsers.add_parser(
        'create',
        help='Create a new item'
    )
    create_parser.add_argument('--name', help='Item name')

    # List subcommand
    list_parser = subparsers.add_parser(
        'list',
        help='List all items'
    )
    list_parser.add_argument('--filter', help='Filter results')

    # Delete subcommand
    delete_parser = subparsers.add_parser(
        'delete',
        help='Delete an item'
    )
    delete_parser.add_argument('id', help='Item ID to delete')

    # Status subcommand
    status_parser = subparsers.add_parser(
        'status',
        help='Show status information'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    print(f"Executing: {args.command}")

if __name__ == '__main__':
    main()
