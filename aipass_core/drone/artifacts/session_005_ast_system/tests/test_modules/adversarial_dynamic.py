#!/usr/bin/env python3
"""
Adversarial Test: Dynamic Choices
Testing: Can AST detect commands when choices are built from variables?
This should FAIL for AST since choices are runtime-generated
"""

import argparse
import sys

# Dynamic choices defined as variables
BACKUP_MODES = ['snapshot', 'versioned', 'incremental', 'differential']
ENVIRONMENTS = ['dev', 'staging', 'prod']

def main():
    parser = argparse.ArgumentParser(
        description='Testing dynamic choices'
    )

    # Choices from variable
    parser.add_argument(
        'mode',
        choices=BACKUP_MODES,
        help='Backup mode to use'
    )

    # Choices from list comprehension
    parser.add_argument(
        'env',
        nargs='?',
        choices=[e for e in ENVIRONMENTS],
        help='Target environment'
    )

    # Choices from function call
    def get_formats():
        return ['json', 'yaml', 'xml']

    parser.add_argument(
        '--format',
        choices=get_formats(),
        help='Output format'
    )

    args = parser.parse_args()
    print(f"Mode: {args.mode}, Env: {args.env}")

if __name__ == '__main__':
    main()
