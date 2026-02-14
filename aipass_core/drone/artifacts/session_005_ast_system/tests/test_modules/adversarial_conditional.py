#!/usr/bin/env python3
"""
Adversarial Test: Conditional Parser Creation
Testing: Can AST detect commands when parser is built conditionally?
This tests if/else blocks, class methods, and conditional logic
"""

import argparse
import sys
import os

class CLIManager:
    """Parser inside a class"""

    def __init__(self, mode='production'):
        self.mode = mode
        self.parser = self._build_parser()

    def _build_parser(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest='command')

        # Always present commands
        subparsers.add_parser('status', help='Show status')
        subparsers.add_parser('version', help='Show version')

        # Conditionally added commands
        if self.mode == 'development':
            subparsers.add_parser('debug', help='Debug mode')
            subparsers.add_parser('test', help='Run tests')
        elif self.mode == 'production':
            subparsers.add_parser('deploy', help='Deploy app')
            subparsers.add_parser('monitor', help='Monitor app')

        return parser

def create_parser_with_conditions():
    """Parser creation with environment checks"""
    parser = argparse.ArgumentParser()

    if os.getenv('ENABLE_ADMIN'):
        parser.add_argument('admin_cmd', choices=['user', 'role', 'config'])

    if sys.platform == 'linux':
        parser.add_argument('--systemd', action='store_true')

    return parser

def main():
    # Which parser to use depends on args
    if '--class-mode' in sys.argv:
        cli = CLIManager()
        parser = cli.parser
    else:
        parser = create_parser_with_conditions()

    args = parser.parse_args()
    print(f"Parsed: {args}")

if __name__ == '__main__':
    main()
