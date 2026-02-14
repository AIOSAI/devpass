#!/usr/bin/env python3
"""
Adversarial Test: Nested Subparsers
Testing: Can AST handle subparsers within subparsers?
"""

import argparse
import sys

def main():
    parser = argparse.ArgumentParser(
        description='Testing nested subparsers'
    )

    # First level subparsers
    subparsers = parser.add_subparsers(
        dest='command',
        help='Main commands'
    )

    # Database command with nested subparsers
    db_parser = subparsers.add_parser(
        'database',
        help='Database operations'
    )

    db_subparsers = db_parser.add_subparsers(
        dest='db_command',
        help='Database sub-commands'
    )

    db_subparsers.add_parser('migrate', help='Run migrations')
    db_subparsers.add_parser('seed', help='Seed database')
    db_subparsers.add_parser('reset', help='Reset database')

    # API command with nested subparsers
    api_parser = subparsers.add_parser(
        'api',
        help='API operations'
    )

    api_subparsers = api_parser.add_subparsers(
        dest='api_command',
        help='API sub-commands'
    )

    api_subparsers.add_parser('start', help='Start API server')
    api_subparsers.add_parser('stop', help='Stop API server')
    api_subparsers.add_parser('status', help='Check API status')

    # Simple command (no nesting)
    subparsers.add_parser('version', help='Show version')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    print(f"Command: {args.command}")

if __name__ == '__main__':
    main()
