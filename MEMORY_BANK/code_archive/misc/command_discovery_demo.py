#!/usr/bin/env python3
"""
Command Discovery Demo - Extracting CLI Commands from Dispatcher Functions

Demonstrates multiple approaches to automatically detect available commands
from Python dispatcher functions using AST analysis.

Author: AIPass Drone
Date: 2025-10-15
"""

import ast
import inspect
from typing import Callable, List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class MatchType(Enum):
    """Types of command matches detected"""
    EXACT = "exact"           # if cmd == "status"
    PREFIX = "prefix"         # if cmd.startswith("deploy")
    SUFFIX = "suffix"         # if cmd.endswith("-all")
    IN_LIST = "in_list"       # if cmd in ["a", "b"]
    CONTAINS = "contains"     # if "keyword" in cmd
    UNKNOWN = "unknown"


@dataclass
class CommandInfo:
    """Metadata about a detected command"""
    command: str
    match_type: MatchType
    line_number: int
    confidence: float  # 0.0-1.0


class CommandExtractor(ast.NodeVisitor):
    """
    AST visitor that extracts command strings from if/elif dispatcher patterns.

    Supports multiple patterns:
    - if cmd == "status"
    - if cmd in ["status", "scan"]
    - if cmd.startswith("deploy")
    - if cmd.endswith("-all")
    - if "keyword" in cmd
    """

    def __init__(self):
        self.commands: List[CommandInfo] = []

    def visit_If(self, node: ast.If):
        """Visit If nodes (includes elif as nested If in orelse)"""
        self._extract_from_test(node.test)

        # Handle elif chains (stored in orelse)
        for else_node in node.orelse:
            if isinstance(else_node, ast.If):
                self.visit(else_node)

        self.generic_visit(node)

    def _extract_from_test(self, test_node: ast.expr):
        """Extract commands from various test patterns"""

        # Pattern 1: if cmd == "status"
        if isinstance(test_node, ast.Compare):
            self._handle_comparison(test_node)

        # Pattern 2: if cmd.startswith("deploy")
        elif isinstance(test_node, ast.Call):
            self._handle_method_call(test_node)

    def _handle_comparison(self, node: ast.Compare):
        """Handle comparison operations (==, in, etc.)"""

        # Pattern: if cmd == "status"
        if any(isinstance(op, ast.Eq) for op in node.ops):
            for comparator in node.comparators:
                if isinstance(comparator, ast.Constant) and isinstance(comparator.value, str):
                    self.commands.append(CommandInfo(
                        command=comparator.value,
                        match_type=MatchType.EXACT,
                        line_number=comparator.lineno,
                        confidence=1.0
                    ))

        # Pattern: if cmd in ["status", "scan"]
        elif any(isinstance(op, ast.In) for op in node.ops):
            for comparator in node.comparators:
                if isinstance(comparator, ast.List):
                    for elt in comparator.elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            self.commands.append(CommandInfo(
                                command=elt.value,
                                match_type=MatchType.IN_LIST,
                                line_number=elt.lineno,
                                confidence=1.0
                            ))

                # Pattern: if "keyword" in cmd (reversed)
                elif isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                    self.commands.append(CommandInfo(
                        command=node.left.value,
                        match_type=MatchType.CONTAINS,
                        line_number=node.lineno,
                        confidence=0.7  # Lower confidence for contains
                    ))

    def _handle_method_call(self, node: ast.Call):
        """Handle string method calls like startswith, endswith"""

        if not isinstance(node.func, ast.Attribute):
            return

        method_name = node.func.attr

        # Pattern: if cmd.startswith("deploy")
        if method_name == "startswith" and node.args:
            if isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                self.commands.append(CommandInfo(
                    command=f"{node.args[0].value}*",  # Mark as prefix
                    match_type=MatchType.PREFIX,
                    line_number=node.lineno,
                    confidence=0.9
                ))

        # Pattern: if cmd.endswith("-all")
        elif method_name == "endswith" and node.args:
            if isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                self.commands.append(CommandInfo(
                    command=f"*{node.args[0].value}",  # Mark as suffix
                    match_type=MatchType.SUFFIX,
                    line_number=node.lineno,
                    confidence=0.9
                ))


def discover_commands(dispatcher_func: Callable) -> Dict[str, Any]:
    """
    Discover commands from a dispatcher function using AST analysis.

    Args:
        dispatcher_func: Function containing if/elif command dispatch logic

    Returns:
        Dict containing:
            - commands: List of command strings
            - details: List of CommandInfo objects with metadata
            - function_name: Name of analyzed function
            - source_file: File containing the function
            - success: Whether analysis succeeded
            - error: Error message if failed

    Example:
        >>> def my_handler(cmd):
        ...     if cmd == "status":
        ...         return "ok"
        ...     elif cmd == "scan":
        ...         return "scanning"
        >>> result = discover_commands(my_handler)
        >>> print(result['commands'])
        ['status', 'scan']
    """
    try:
        # Get source code
        source = inspect.getsource(dispatcher_func)

        # Parse into AST
        tree = ast.parse(source)

        # Extract commands
        extractor = CommandExtractor()
        extractor.visit(tree)

        # Sort by line number for consistent ordering
        details = sorted(extractor.commands, key=lambda x: x.line_number)

        # Get unique command strings
        commands = []
        seen = set()
        for info in details:
            if info.command not in seen:
                commands.append(info.command)
                seen.add(info.command)

        return {
            'success': True,
            'commands': commands,
            'details': details,
            'function_name': dispatcher_func.__name__,
            'source_file': inspect.getfile(dispatcher_func),
            'total_found': len(details),
            'unique_commands': len(commands)
        }

    except Exception as e:
        return {
            'success': False,
            'commands': [],
            'details': [],
            'error': str(e),
            'function_name': getattr(dispatcher_func, '__name__', 'unknown')
        }


# ============================================================================
# DEMO FUNCTIONS - Various Dispatcher Patterns
# ============================================================================

def simple_dispatcher(cmd: str):
    """Simple if/elif chain with exact matches"""
    if cmd == "status":
        return "System is running"
    elif cmd == "scan":
        return "Scanning..."
    elif cmd == "quit":
        return "Goodbye"
    else:
        return "Unknown command"


def list_dispatcher(cmd: str):
    """Using 'in' with list of commands"""
    if cmd in ["start", "run", "begin"]:
        return "Starting..."
    elif cmd in ["stop", "halt", "end"]:
        return "Stopping..."
    elif cmd == "status":
        return "Running"
    else:
        return "Unknown"


def prefix_dispatcher(cmd: str):
    """Using startswith for command families"""
    if cmd.startswith("deploy"):
        return f"Deploying: {cmd}"
    elif cmd.startswith("test"):
        return f"Testing: {cmd}"
    elif cmd == "status":
        return "OK"
    else:
        return "Unknown"


def mixed_dispatcher(cmd: str):
    """Mix of exact, prefix, and list patterns"""
    if cmd == "help":
        return "Help text"
    elif cmd.startswith("get-"):
        return f"Getting {cmd[4:]}"
    elif cmd in ["quit", "exit", "q"]:
        return "Exiting"
    elif cmd.endswith("-all"):
        return f"Processing all: {cmd}"
    else:
        return "Unknown"


def complex_dispatcher(cmd: str):
    """More complex patterns (some may not be detected)"""
    if cmd == "status":
        return "OK"
    elif cmd.lower() == "help":  # Transformed comparison
        return "Help"
    elif cmd.startswith("deploy-"):
        return "Deploying"
    elif "debug" in cmd:  # Contains pattern
        return "Debug mode"
    else:
        return "Unknown"


# ============================================================================
# DEMO / TEST FUNCTIONS
# ============================================================================

def print_results(func: Callable, show_details: bool = False):
    """Pretty print discovery results for a function"""
    print(f"\n{'='*70}")
    print(f"Analyzing: {func.__name__}")
    print(f"{'='*70}")

    result = discover_commands(func)

    if result['success']:
        print(f"✓ Success! Found {result['unique_commands']} unique commands")
        print(f"\nCommands detected:")
        for cmd in result['commands']:
            print(f"  - {cmd}")

        if show_details:
            print(f"\nDetailed info:")
            for detail in result['details']:
                print(f"  Line {detail.line_number}: '{detail.command}' "
                      f"({detail.match_type.value}, confidence: {detail.confidence:.0%})")
    else:
        print(f"✗ Failed: {result['error']}")

    return result


def run_all_demos():
    """Run discovery on all demo functions"""
    print("="*70)
    print("CLI Command Discovery Demo")
    print("="*70)

    demo_functions = [
        simple_dispatcher,
        list_dispatcher,
        prefix_dispatcher,
        mixed_dispatcher,
        complex_dispatcher,
    ]

    results = []
    for func in demo_functions:
        result = print_results(func, show_details=True)
        results.append(result)

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    total_commands = sum(r['unique_commands'] for r in results if r['success'])
    successful = sum(1 for r in results if r['success'])
    print(f"Analyzed {len(demo_functions)} functions")
    print(f"Success rate: {successful}/{len(demo_functions)} ({successful/len(demo_functions)*100:.0f}%)")
    print(f"Total unique commands found: {total_commands}")


def test_specific_function():
    """Test a specific function and return structured data"""
    result = discover_commands(mixed_dispatcher)

    # Show how to use the results programmatically
    if result['success']:
        print("\nProgrammatic usage example:")
        print(f"Function: {result['function_name']}")
        print(f"Commands: {', '.join(result['commands'])}")

        # Filter by match type
        exact_matches = [d for d in result['details'] if d.match_type == MatchType.EXACT]
        prefix_matches = [d for d in result['details'] if d.match_type == MatchType.PREFIX]

        print(f"Exact matches: {[d.command for d in exact_matches]}")
        print(f"Prefix matches: {[d.command for d in prefix_matches]}")


if __name__ == "__main__":
    # Run all demos
    run_all_demos()

    # Show specific example
    print("\n" + "="*70)
    print("PROGRAMMATIC USAGE EXAMPLE")
    print("="*70)
    test_specific_function()

    # Integration example
    print("\n" + "="*70)
    print("INTEGRATION EXAMPLE")
    print("="*70)
    print("""
    # How to use in your CLI:

    from command_discovery_demo import discover_commands

    def my_command_handler(cmd: str):
        if cmd == "help":
            # Auto-generate help from discovered commands
            result = discover_commands(my_command_handler)
            print("Available commands:")
            for cmd in result['commands']:
                print(f"  - {cmd}")
        elif cmd == "deploy":
            deploy_app()
        # ... etc

    # Or use it for validation:
    result = discover_commands(my_command_handler)
    valid_commands = set(result['commands'])

    user_input = input("Enter command: ")
    if user_input not in valid_commands:
        print(f"Invalid command. Try: {', '.join(valid_commands)}")
    """)
