#!/usr/bin/env python3
"""
Adversarial Test: Edge Cases and Complex Strings
Testing: Multi-line help, unicode, special characters, missing help, weird formatting
"""

import argparse
import sys

def main():
    parser = argparse.ArgumentParser(
        description='Testing edge cases'
    )

    subparsers = parser.add_subparsers(dest='command')

    # Multi-line help text
    subparsers.add_parser(
        'deploy',
        help="""Deploy the application to production.
        This will build, test, and push to remote servers.
        Use with caution in production environments."""
    )

    # Unicode in help text
    subparsers.add_parser(
        'backup',
        help='Create backup 📦 of the database 💾'
    )

    # Special characters in help
    subparsers.add_parser(
        'query',
        help='Execute SQL query (use "quotes" & \'apostrophes\')'
    )

    # No help text at all
    subparsers.add_parser('status')

    # Empty string help
    subparsers.add_parser('ping', help='')

    # Very long help text
    subparsers.add_parser(
        'migrate',
        help='Run database migrations and update schema version tracking system with rollback capabilities and transaction management for production databases with replication support'
    )

    # Weird spacing and formatting
    subparsers.add_parser('clean'  ,  help  =  'Clean temporary files'  )

    # Single vs double quotes mixing
    subparsers.add_parser("build", help='Build the project')
    subparsers.add_parser('test', help="Run all tests")

    # Command name with underscore
    subparsers.add_parser('run_server', help='Start the server')

    # Command name with dash
    subparsers.add_parser('check-health', help='Check system health')

    args = parser.parse_args()
    print(f"Command: {args.command}")

if __name__ == '__main__':
    main()
