#!/usr/bin/env python3
"""
CLI Layout Demo - Visual examples of proposed standard layouts
Run this to see what the CLI output would look like
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import track
import time

console = Console()

# Clear screen and show demo
console.clear()

# ============================================================================
# Example 1: Flow - Create Plan
# ============================================================================
console.print(Panel("[bold cyan]Flow - Plan Manager[/bold cyan]", expand=False))
console.print()

console.print("⚙️  [blue]Creating new plan...[/blue]")
console.print()

console.print("✅ [green]Plan created successfully[/green]")
console.print("   [dim]ID: PLAN0123[/dim]")
console.print("   [dim]Path: /home/aipass/flow/plans/PLAN0123.md[/dim]")
console.print()

console.print("✅ [green]Plan registry updated[/green]")
console.print()

console.print("─" * 50)
console.print("[bold]Summary:[/bold]")
console.print("  ✅ 2 operations succeeded")
console.print("  [dim]Completed in 0.3s[/dim]")
console.print()

input("Press Enter to see next example...")
console.clear()

# ============================================================================
# Example 2: Cortex - Create Branch (with warnings/errors)
# ============================================================================
console.print(Panel("[bold cyan]Cortex - Branch Manager[/bold cyan]", expand=False))
console.print()

console.print("⚙️  [blue]Creating branch from template...[/blue]")
console.print()

console.print("✅ [green]Directory created[/green]")
console.print("   [dim]/home/aipass/aipass_core/new_branch[/dim]")
console.print()

console.print("✅ [green]Files copied[/green]")
console.print("   [dim]12 files copied from template[/dim]")
console.print()

console.print("⚠️  [yellow]Warning: Template version mismatch[/yellow]")
console.print("   [dim]Expected v2.1, found v2.0[/dim]")
console.print("   [dim]Some features may not be available[/dim]")
console.print()

console.print("✅ [green]Registry updated[/green]")
console.print()

console.print("❌ [red bold]Error: Cannot create virtual environment[/red bold]")
console.print("   [dim]Reason: python3-venv not installed[/dim]")
console.print("   [yellow]→ Try: sudo apt install python3-venv[/yellow]")
console.print()

console.print("─" * 50)
console.print("[bold]Summary:[/bold]")
console.print("  ✅ 3 operations succeeded")
console.print("  ⚠️  1 warning")
console.print("  ❌ 1 error")
console.print("  [dim]Completed in 2.1s[/dim]")
console.print()

input("Press Enter to see next example...")
console.clear()

# ============================================================================
# Example 3: Table Output (Branch Registry)
# ============================================================================
console.print(Panel("[bold cyan]Cortex - Branch Registry[/bold cyan]", expand=False))
console.print()

table = Table(title="Active Branches", show_header=True, header_style="bold cyan")
table.add_column("Name", style="cyan", width=20)
table.add_column("Profile", style="green", width=15)
table.add_column("Status", width=12)
table.add_column("Last Updated", style="dim", width=12)

table.add_row("flow", "Plan Manager", "✅ Active", "2025-11-10")
table.add_row("cortex", "Branch Manager", "✅ Active", "2025-11-10")
table.add_row("prax", "Logging Service", "⚠️  Warning", "2025-11-08")
table.add_row("api", "API Service", "✅ Active", "2025-11-09")
table.add_row("drone", "Command Router", "❌ Offline", "2025-11-05")

console.print(table)
console.print()

input("Press Enter to see next example...")
console.clear()

# ============================================================================
# Example 4: Progress Indicator
# ============================================================================
console.print(Panel("[bold cyan]Backup System - Creating Backup[/bold cyan]", expand=False))
console.print()

items = ["flow", "cortex", "prax", "api", "drone", "ai_mail"]

for item in track(items, description="[blue]Backing up branches...[/blue]"):
    time.sleep(0.5)  # Simulate work

console.print()
console.print("✅ [green]Backup completed successfully[/green]")
console.print("   [dim]6 branches backed up[/dim]")
console.print("   [dim]Archive: /home/aipass/backups/backup_2025-11-10.tar.gz[/dim]")
console.print()

input("Press Enter to see next example...")
console.clear()

# ============================================================================
# Example 5: Multi-Operation Output (Detailed)
# ============================================================================
console.print(Panel("[bold cyan]AI Mail - Sending Messages[/bold cyan]", expand=False))
console.print()

console.print("📧 [blue]Sending message to Flow...[/blue]")
console.print("   ✅ [green]Delivered[/green]")
console.print()

console.print("📧 [blue]Sending message to Cortex...[/blue]")
console.print("   ✅ [green]Delivered[/green]")
console.print()

console.print("📧 [blue]Sending message to PRAX...[/blue]")
console.print("   ❌ [red]Failed: Recipient offline[/red]")
console.print("   [dim]Message queued for retry[/dim]")
console.print()

console.print("📧 [blue]Sending message to Drone...[/blue]")
console.print("   ✅ [green]Delivered[/green]")
console.print()

console.print("─" * 50)
console.print("[bold]Summary:[/bold]")
console.print("  ✅ 3 delivered")
console.print("  ❌ 1 failed (queued)")
console.print("  [dim]Completed in 1.2s[/dim]")
console.print()

input("Press Enter to see final example...")
console.clear()

# ============================================================================
# Example 6: Nested Operations with Details
# ============================================================================
console.print(Panel("[bold cyan]Flow - Update All Plans[/bold cyan]", expand=False))
console.print()

console.print("🔍 [blue]Scanning for plans...[/blue]")
console.print("   [dim]Found 5 plans[/dim]")
console.print()

console.print("[bold]Processing plans:[/bold]")
console.print()

console.print("  📝 PLAN0001")
console.print("     ✅ [green]Updated[/green]")
console.print()

console.print("  📝 PLAN0002")
console.print("     ✅ [green]Updated[/green]")
console.print()

console.print("  📝 PLAN0003")
console.print("     ⏭️  [dim]Skipped (closed)[/dim]")
console.print()

console.print("  📝 PLAN0004")
console.print("     ✅ [green]Updated[/green]")
console.print()

console.print("  📝 PLAN0005")
console.print("     ⚠️  [yellow]Warning: Missing metadata[/yellow]")
console.print("     [dim]Plan updated with defaults[/dim]")
console.print()

console.print("─" * 50)
console.print("[bold]Summary:[/bold]")
console.print("  ✅ 4 plans updated")
console.print("  ⏭️  1 plan skipped")
console.print("  ⚠️  1 warning")
console.print("  [dim]Completed in 0.8s[/dim]")
console.print()

console.print("\n[bold green]Output demos complete![/bold green] These are the proposed standard layouts.")
console.print("[dim]All modules would use this consistent format.[/dim]")

input("\nPress Enter to see INTERACTIVE menu examples...")
console.clear()

# ============================================================================
# INTERACTIVE SECTION - Menu Examples
# ============================================================================
console.print(Panel("[bold magenta]Interactive CLI Demos[/bold magenta]", expand=False))
console.print()
console.print("[bold]Now showing interactive menu systems with arrow-key navigation[/bold]")
console.print()

# Check if libraries are installed
try:
    import questionary
    questionary_available = True
except ImportError:
    questionary_available = False

try:
    import inquirer
    inquirer_available = True
except ImportError:
    inquirer_available = False

try:
    from simple_term_menu import TerminalMenu
    simple_menu_available = True
except ImportError:
    simple_menu_available = False

if not questionary_available:
    console.print("⚠️  [yellow]questionary not installed[/yellow]")
    console.print("   [dim]Install: pip install questionary[/dim]")
    console.print()

if not inquirer_available:
    console.print("⚠️  [yellow]inquirer not installed[/yellow]")
    console.print("   [dim]Install: pip install inquirer[/dim]")
    console.print()

if not simple_menu_available:
    console.print("⚠️  [yellow]simple-term-menu not installed[/yellow]")
    console.print("   [dim]Install: pip install simple-term-menu[/dim]")
    console.print()

if not (questionary_available or inquirer_available or simple_menu_available):
    console.print("❌ [red]No interactive menu libraries installed[/red]")
    console.print("[yellow]Install at least one to see interactive demos:[/yellow]")
    console.print("  pip install questionary")
    console.print("  pip install inquirer")
    console.print("  pip install simple-term-menu")
    exit(0)

input("Press Enter to continue...")
console.clear()

# ============================================================================
# Example 7: questionary - Arrow-key selection menu
# ============================================================================
if questionary_available:
    console.print(Panel("[bold magenta]Example 1: questionary - Select Menu[/bold magenta]", expand=False))
    console.print()
    console.print("[bold cyan]Library:[/bold cyan] questionary (Modern, recommended)")
    console.print("[bold cyan]Feature:[/bold cyan] Arrow keys to navigate, Enter to select")
    console.print()

    choice = questionary.select(
        "What do you want to do?",
        choices=[
            "Create Plan",
            "View Plans",
            "Close Plan",
            "Exit Demo"
        ]
    ).ask()

    console.print()
    console.print(f"✅ [green]You selected:[/green] {choice}")
    console.print()

    input("Press Enter to see next example...")
    console.clear()

# ============================================================================
# Example 8: questionary - Checkbox (multi-select)
# ============================================================================
if questionary_available:
    console.print(Panel("[bold magenta]Example 2: questionary - Checkbox (Multi-Select)[/bold magenta]", expand=False))
    console.print()
    console.print("[bold cyan]Feature:[/bold cyan] Arrow keys to navigate, Space to select, Enter to confirm")
    console.print()

    branches = questionary.checkbox(
        "Select branches to update:",
        choices=[
            "flow",
            "cortex",
            "prax",
            "api",
            "drone"
        ]
    ).ask()

    console.print()
    if branches:
        console.print(f"✅ [green]Selected branches:[/green]")
        for branch in branches:
            console.print(f"   • {branch}")
    else:
        console.print("⚠️  [yellow]No branches selected[/yellow]")
    console.print()

    input("Press Enter to see next example...")
    console.clear()

# ============================================================================
# Example 9: questionary - Confirmation prompt
# ============================================================================
if questionary_available:
    console.print(Panel("[bold magenta]Example 3: questionary - Confirmation[/bold magenta]", expand=False))
    console.print()

    confirmed = questionary.confirm("Do you want to proceed with the update?").ask()

    console.print()
    if confirmed:
        console.print("✅ [green]Confirmed - proceeding with update[/green]")
    else:
        console.print("❌ [red]Cancelled - operation aborted[/red]")
    console.print()

    input("Press Enter to see next example...")
    console.clear()

# ============================================================================
# Example 10: inquirer - Alternative menu system
# ============================================================================
if inquirer_available:
    console.print(Panel("[bold magenta]Example 4: inquirer - Classic Menu[/bold magenta]", expand=False))
    console.print()
    console.print("[bold cyan]Library:[/bold cyan] inquirer (Older but proven)")
    console.print("[bold cyan]Feature:[/bold cyan] Arrow keys, Enter to select")
    console.print()

    questions = [
        inquirer.List('module',
                      message="Which module do you want to work with?",
                      choices=['Flow', 'Cortex', 'PRAX', 'API', 'Drone'],
                  ),
    ]
    answers = inquirer.prompt(questions)

    console.print()
    console.print(f"✅ [green]You selected:[/green] {answers['module']}")
    console.print()

    input("Press Enter to see next example...")
    console.clear()

# ============================================================================
# Example 11: simple-term-menu - Lightweight option
# ============================================================================
if simple_menu_available:
    console.print(Panel("[bold magenta]Example 5: simple-term-menu - Lightweight[/bold magenta]", expand=False))
    console.print()
    console.print("[bold cyan]Library:[/bold cyan] simple-term-menu (Minimal, fast)")
    console.print("[bold cyan]Feature:[/bold cyan] Arrow keys, Enter to select")
    console.print()

    options = ["Create Branch", "Update Branch", "Delete Branch", "List Branches"]
    terminal_menu = TerminalMenu(options, title="Cortex - Branch Manager")
    choice_index = terminal_menu.show()

    if choice_index is not None:
        console.print()
        console.print(f"✅ [green]You selected:[/green] {options[choice_index]}")
        console.print()

    input("Press Enter to see next example...")
    console.clear()

# ============================================================================
# Example 12: Rich + questionary Combined - Full workflow
# ============================================================================
if questionary_available:
    console.print(Panel("[bold magenta]Example 6: Rich + questionary Combined[/bold magenta]", expand=False))
    console.print()
    console.print("[bold]This shows how to combine Rich (output) + questionary (input)[/bold]")
    console.print("[dim]Multi-page interactive workflow demonstration[/dim]")
    console.print()

    input("Press Enter to start interactive flow...")
    console.clear()

    # Page 1: Main menu
    console.print(Panel("[bold cyan]Flow - Plan Manager[/bold cyan]", expand=False))
    console.print()

    action = questionary.select(
        "What would you like to do?",
        choices=[
            "Create new plan",
            "View existing plans",
            "Close a plan",
            "Exit"
        ]
    ).ask()

    console.clear()

    # Page 2: Based on selection
    if action == "Create new plan":
        console.print(Panel("[bold cyan]Flow - Create Plan[/bold cyan]", expand=False))
        console.print()

        plan_name = questionary.text("Plan name:").ask()
        plan_type = questionary.select(
            "Plan type:",
            choices=["Development", "Bug Fix", "Feature", "Research"]
        ).ask()

        console.clear()

        # Page 3: Confirmation
        console.print(Panel("[bold cyan]Flow - Confirm Plan Creation[/bold cyan]", expand=False))
        console.print()
        console.print(f"[bold]Plan Details:[/bold]")
        console.print(f"  Name: {plan_name}")
        console.print(f"  Type: {plan_type}")
        console.print()

        confirmed = questionary.confirm("Create this plan?").ask()

        console.clear()

        # Page 4: Results with Rich formatting
        console.print(Panel("[bold cyan]Flow - Create Plan[/bold cyan]", expand=False))
        console.print()

        if confirmed:
            console.print("⚙️  [blue]Creating plan...[/blue]")
            console.print()
            time.sleep(1)

            console.print("✅ [green]Plan created successfully[/green]")
            console.print(f"   [dim]Name: {plan_name}[/dim]")
            console.print(f"   [dim]Type: {plan_type}[/dim]")
            console.print(f"   [dim]ID: PLAN{hash(plan_name) % 10000:04d}[/dim]")
            console.print()

            console.print("─" * 50)
            console.print("[bold]Summary:[/bold]")
            console.print("  ✅ Plan created")
            console.print("  ✅ Registry updated")
            console.print("  [dim]Completed in 0.2s[/dim]")
        else:
            console.print("❌ [red]Plan creation cancelled[/red]")

        console.print()

    elif action == "View existing plans":
        console.print(Panel("[bold cyan]Flow - Plan List[/bold cyan]", expand=False))
        console.print()

        # Mock data for demo
        table = Table(title="Active Plans", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="cyan", width=10)
        table.add_column("Name", style="white", width=25)
        table.add_column("Type", style="green", width=15)
        table.add_column("Status", width=12)

        table.add_row("PLAN0001", "CLI Layout System", "Feature", "✅ Active")
        table.add_row("PLAN0002", "Handler Marketplace", "Development", "✅ Active")
        table.add_row("PLAN0003", "Bug Fix #42", "Bug Fix", "⚠️  Blocked")

        console.print(table)
        console.print()

    elif action == "Close a plan":
        console.print(Panel("[bold cyan]Flow - Close Plan[/bold cyan]", expand=False))
        console.print()

        plan_to_close = questionary.select(
            "Select plan to close:",
            choices=["PLAN0001 - CLI Layout System", "PLAN0002 - Handler Marketplace", "Cancel"]
        ).ask()

        if plan_to_close != "Cancel":
            console.clear()
            console.print(Panel("[bold cyan]Flow - Close Plan[/bold cyan]", expand=False))
            console.print()
            console.print(f"✅ [green]Plan closed:[/green] {plan_to_close.split(' - ')[0]}")
            console.print("   [dim]Moved to closed plans archive[/dim]")
            console.print()

    else:  # Exit
        console.print("👋 [blue]Exiting...[/blue]")

    console.print()

console.print("\n[bold green]Interactive demo complete![/bold green]")
console.print()
console.print("[bold]Key Takeaways:[/bold]")
console.print("  • [cyan]questionary[/cyan] - Modern, best for new projects")
console.print("  • [cyan]inquirer[/cyan] - Classic, proven")
console.print("  • [cyan]simple-term-menu[/cyan] - Lightweight, minimal")
console.print("  • [cyan]Rich + questionary[/cyan] - Best combination (output + input)")
console.print()
console.print("[yellow]You can design entire interactive workflows visually![/yellow]")
console.print("[dim]Build the prototype here, then implement in modules[/dim]")
