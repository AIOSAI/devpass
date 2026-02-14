#!/usr/bin/env python3
"""
Real-world CLI Integration Example

Shows how to use command discovery for:
1. Auto-generated help text
2. Command validation
3. Tab completion support
4. Command documentation

Author: AIPass Drone
Date: 2025-10-15
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from command_discovery_demo import discover_commands, MatchType


class AutoDiscoveryCLI:
    """
    CLI that automatically discovers its own commands using AST analysis.

    This demonstrates how to use command discovery in a real CLI application.
    """

    def __init__(self):
        # Discover commands on initialization
        self.available_commands = self._discover_my_commands()

    def _discover_my_commands(self):
        """Discover commands from the handle_command method"""
        result = discover_commands(self.handle_command)
        if result['success']:
            return {
                'all': result['commands'],
                'exact': [d.command for d in result['details'] if d.match_type == MatchType.EXACT],
                'prefix': [d.command for d in result['details'] if d.match_type == MatchType.PREFIX],
                'details': result['details']
            }
        return {'all': [], 'exact': [], 'prefix': [], 'details': []}

    def handle_command(self, cmd: str) -> str:
        """
        Main command dispatcher.

        Commands are auto-discovered from this function!
        """
        if cmd == "help":
            return self.show_help()

        elif cmd == "status":
            return "System Status: OK\nUptime: 42 days\nMemory: 60% used"

        elif cmd == "scan":
            return "Scanning...\nFound 15 items\nScan complete!"

        elif cmd in ["quit", "exit", "q"]:
            return "Goodbye!"

        elif cmd.startswith("deploy-"):
            app_name = cmd[7:]  # Remove "deploy-" prefix
            return f"Deploying application: {app_name}\nDeployment in progress..."

        elif cmd.startswith("test-"):
            test_name = cmd[5:]  # Remove "test-" prefix
            return f"Running tests for: {test_name}\nAll tests passed!"

        elif cmd == "version":
            return "AutoDiscoveryCLI v1.0.0"

        elif cmd == "list":
            return self.list_commands()

        else:
            return f"Unknown command: '{cmd}'\nTry 'help' for available commands."

    def show_help(self) -> str:
        """Auto-generated help based on discovered commands"""
        help_text = ["Available Commands:", "=" * 50]

        # Group by match type
        exact_cmds = sorted([c for c in self.available_commands['exact']
                            if c not in ['help', 'list']])
        prefix_cmds = sorted(set([d.command for d in self.available_commands['details']
                                 if d.match_type == MatchType.PREFIX]))

        # Exact match commands
        if exact_cmds:
            help_text.append("\nDirect Commands:")
            for cmd in exact_cmds:
                help_text.append(f"  {cmd:<15} - Execute {cmd} command")

        # Prefix commands (command families)
        if prefix_cmds:
            help_text.append("\nCommand Families:")
            for cmd in prefix_cmds:
                base = cmd.rstrip('*')
                help_text.append(f"  {cmd:<15} - {base} operations (e.g., {base}app)")

        # Meta commands
        help_text.append("\nUtility Commands:")
        help_text.append(f"  {'help':<15} - Show this help message")
        help_text.append(f"  {'list':<15} - List all discovered commands")
        help_text.append(f"  {'quit/exit/q':<15} - Exit the CLI")

        return "\n".join(help_text)

    def list_commands(self) -> str:
        """List all auto-discovered commands with metadata"""
        lines = [
            "Auto-Discovered Commands:",
            "=" * 70,
            ""
        ]

        for detail in sorted(self.available_commands['details'], key=lambda x: x.line_number):
            match_type = detail.match_type.value
            confidence = f"{detail.confidence:.0%}"
            lines.append(f"  {detail.command:<20} [{match_type:<10}] {confidence} confidence")

        lines.append("")
        lines.append(f"Total: {len(self.available_commands['details'])} command patterns detected")
        lines.append(f"Unique: {len(self.available_commands['all'])} unique commands")

        return "\n".join(lines)

    def validate_command(self, cmd: str) -> tuple[bool, str]:
        """
        Validate if a command is recognized.

        Returns: (is_valid, message)
        """
        # Check exact matches
        if cmd in self.available_commands['exact']:
            return True, f"Valid command: {cmd}"

        # Check prefix matches
        for prefix in self.available_commands['prefix']:
            if prefix.endswith('*') and cmd.startswith(prefix[:-1]):
                return True, f"Valid command family: {prefix}"

        # Check exit aliases
        if cmd in ['quit', 'exit', 'q']:
            return True, "Valid exit command"

        return False, f"Unknown command: '{cmd}'"

    def get_suggestions(self, partial_cmd: str) -> list[str]:
        """Get command suggestions for tab completion"""
        suggestions = []

        # Find exact matches that start with the partial command
        for cmd in self.available_commands['exact']:
            if cmd.startswith(partial_cmd):
                suggestions.append(cmd)

        # Handle prefix patterns
        for detail in self.available_commands['details']:
            if detail.match_type == MatchType.PREFIX:
                base = detail.command.rstrip('*')
                if base.startswith(partial_cmd):
                    suggestions.append(f"{base}app")  # Example completion
                    suggestions.append(f"{base}service")

        return sorted(set(suggestions))

    def run_interactive(self):
        """Run interactive CLI loop"""
        print("AutoDiscoveryCLI - Interactive Mode")
        print("Type 'help' for available commands, 'quit' to exit\n")

        while True:
            try:
                cmd = input("cli> ").strip()

                if not cmd:
                    continue

                # Execute command
                result = self.handle_command(cmd)
                print(result)

                # Exit on quit commands
                if cmd in ['quit', 'exit', 'q']:
                    break

            except KeyboardInterrupt:
                print("\n\nInterrupted. Type 'quit' to exit.")
            except EOFError:
                print("\nGoodbye!")
                break


def demo_validation():
    """Demonstrate command validation"""
    print("=" * 70)
    print("COMMAND VALIDATION DEMO")
    print("=" * 70)

    cli = AutoDiscoveryCLI()

    test_commands = [
        "status",          # Valid exact
        "scan",            # Valid exact
        "deploy-myapp",    # Valid prefix
        "test-auth",       # Valid prefix
        "invalid",         # Invalid
        "deploy",          # Invalid (needs suffix)
    ]

    for cmd in test_commands:
        is_valid, msg = cli.validate_command(cmd)
        status = "✓" if is_valid else "✗"
        print(f"{status} {cmd:<20} - {msg}")


def demo_suggestions():
    """Demonstrate tab completion suggestions"""
    print("\n" + "=" * 70)
    print("TAB COMPLETION DEMO")
    print("=" * 70)

    cli = AutoDiscoveryCLI()

    partials = ["st", "de", "test", "q"]

    for partial in partials:
        suggestions = cli.get_suggestions(partial)
        if suggestions:
            print(f"'{partial}' -> {', '.join(suggestions)}")
        else:
            print(f"'{partial}' -> (no suggestions)")


def demo_auto_help():
    """Demonstrate auto-generated help"""
    print("\n" + "=" * 70)
    print("AUTO-GENERATED HELP DEMO")
    print("=" * 70)

    cli = AutoDiscoveryCLI()
    print(cli.show_help())


def demo_command_list():
    """Demonstrate command listing with metadata"""
    print("\n" + "=" * 70)
    print("COMMAND LIST WITH METADATA")
    print("=" * 70)

    cli = AutoDiscoveryCLI()
    print(cli.list_commands())


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        # Run interactive mode
        cli = AutoDiscoveryCLI()
        cli.run_interactive()
    else:
        # Run demos
        print("AutoDiscoveryCLI - Integration Examples\n")
        demo_auto_help()
        demo_command_list()
        demo_validation()
        demo_suggestions()

        print("\n" + "=" * 70)
        print("TRY INTERACTIVE MODE")
        print("=" * 70)
        print("Run: python3 cli_integration_example.py interactive")
