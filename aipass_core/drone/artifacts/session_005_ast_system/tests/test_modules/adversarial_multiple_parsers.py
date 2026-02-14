#!/usr/bin/env python3
"""
Adversarial Test: Multiple Parsers
Testing: What happens when there are multiple ArgumentParser instances?
Which one does AST detect?
"""

import argparse
import sys

# First parser - for main CLI
def create_main_parser():
    parser = argparse.ArgumentParser(
        description='Main CLI parser'
    )
    parser.add_argument(
        'action',
        choices=['start', 'stop', 'restart'],
        help='Main action'
    )
    return parser

# Second parser - for admin CLI
def create_admin_parser():
    parser = argparse.ArgumentParser(
        description='Admin CLI parser'
    )
    subparsers = parser.add_subparsers(dest='admin_command')
    subparsers.add_parser('users', help='Manage users')
    subparsers.add_parser('roles', help='Manage roles')
    subparsers.add_parser('audit', help='View audit logs')
    return parser

# Third parser - for testing
TEST_PARSER = argparse.ArgumentParser()
TEST_PARSER.add_argument('test', choices=['unit', 'integration', 'e2e'])

def main():
    # Which parser gets used depends on environment variable
    import os
    mode = os.getenv('CLI_MODE', 'main')

    if mode == 'admin':
        parser = create_admin_parser()
    elif mode == 'test':
        parser = TEST_PARSER
    else:
        parser = create_main_parser()

    args = parser.parse_args()
    print(f"Parsed: {args}")

if __name__ == '__main__':
    main()
