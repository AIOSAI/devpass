#!/usr/bin/env python3
"""
Adversarial Test: Loop-Generated Commands
Testing: Can AST detect commands added in a loop?
This should FAIL for AST since commands are runtime-generated
"""

import argparse
import sys

def main():
    parser = argparse.ArgumentParser(
        description='Testing loop-generated commands'
    )

    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands'
    )

    # Commands generated in a loop
    operations = [
        ('create', 'Create a new resource'),
        ('read', 'Read a resource'),
        ('update', 'Update a resource'),
        ('delete', 'Delete a resource'),
        ('list', 'List all resources'),
    ]

    for cmd_name, cmd_help in operations:
        subparsers.add_parser(cmd_name, help=cmd_help)

    # Another loop with comprehension-style
    for status in ['pending', 'active', 'completed', 'failed']:
        subparsers.add_parser(
            f'filter_{status}',
            help=f'Filter by {status} status'
        )

    args = parser.parse_args()
    print(f"Command: {args.command}")

if __name__ == '__main__':
    main()
