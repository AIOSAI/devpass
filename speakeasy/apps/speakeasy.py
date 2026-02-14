#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: speakeasy.py - SPEAKEASY Branch Entry Point
# Date: 2026-02-11
# Version: 1.0.0
# Category: speakeasy
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-11): Initial branch creation
#
# CODE STANDARDS:
#   - Handlers implement logic, modules orchestrate
# =============================================

"""
SPEAKEASY Branch - Main Orchestrator

Auto-discovery architecture:
- Scans modules/ directory for .py files with handle_command()
- Routes commands to discovered modules automatically
- No manual imports or routing needed
"""

# INFRASTRUCTURE IMPORT PATTERN
import sys
from pathlib import Path
AIPASS_ROOT = Path.home() / "aipass_core"
sys.path.insert(0, str(AIPASS_ROOT))

# Standard library imports
import importlib
from typing import List, Any

# Prax logger
from prax.apps.modules.logger import system_logger as logger

# CLI services for formatted output
from cli.apps.modules import console, header

# =============================================================================
# MODULE DISCOVERY
# =============================================================================

MODULES_DIR = Path(__file__).parent / "modules"

def discover_modules() -> List[Any]:
    """
    Auto-discover modules in modules/ directory

    Modules must implement handle_command(command: str, args: List[str]) -> bool

    Returns:
        List of module objects with handle_command function
    """
    modules = []

    if not MODULES_DIR.exists():
        logger.warning(f"[SPEAKEASY] Modules directory not found: {MODULES_DIR}")
        return modules

    # Add modules directory to path for imports
    modules_parent = MODULES_DIR.parent
    if str(modules_parent) not in sys.path:
        sys.path.insert(0, str(modules_parent))

    # Discover all .py files (except __init__.py and those starting with _)
    for file_path in MODULES_DIR.glob("*.py"):
        if file_path.name.startswith("_"):
            continue

        module_name = f"modules.{file_path.stem}"

        try:
            module = importlib.import_module(module_name)

            # Check if module has handle_command function
            if hasattr(module, 'handle_command'):
                modules.append(module)
                logger.info(f"[SPEAKEASY] Loaded module: {file_path.stem}")
            else:
                logger.info(f"[SPEAKEASY] Skipped {file_path.stem} - no handle_command()")

        except Exception as e:
            logger.error(f"[SPEAKEASY] Failed to load module {module_name}: {e}")

    return modules


def route_command(command: str, args: List[str], modules: List[Any]) -> bool:
    """
    Route command to appropriate module

    Args:
        command: Command name (e.g., 'create', 'update', 'list')
        args: Additional arguments
        modules: List of discovered modules

    Returns:
        True if command was handled, False otherwise
    """
    for module in modules:
        try:
            if module.handle_command(command, args):
                return True
        except Exception as e:
            logger.error(f"[SPEAKEASY] Module {module.__name__} error: {e}")

    return False

# =============================================================================
# INTROSPECTION DISPLAY
# =============================================================================

def print_introspection(modules: List[Any]):
    """Display discovered modules when run without arguments"""
    console.print()
    console.print("[bold cyan]SPEAKEASY - Branch Management System[/bold cyan]")
    console.print()
    console.print("[dim]Auto-discovered module orchestration[/dim]")
    console.print()

    console.print(f"[yellow]Discovered Modules:[/yellow] {len(modules)}")
    console.print()

    if modules:
        for module in modules:
            module_name = module.__name__.split('.')[-1]
            # Get first line of docstring
            description = "No description"
            if module.__doc__:
                description = module.__doc__.strip().split('\n')[0]
            console.print(f"  [cyan]•[/cyan] {module_name:20} [dim]{description}[/dim]")
    else:
        console.print("  [dim]No modules discovered[/dim]")

    console.print()
    console.print("[dim]Run 'python3 speakeasy.py --help' for usage information[/dim]")
    console.print()


# =============================================================================
# DRONE COMPLIANCE - HELP SYSTEM
# =============================================================================

def print_help(modules: List[Any]):
    """Display Rich-formatted help"""
    console.print()
    header("SPEAKEASY - Branch Management System")
    console.print()

    console.print("[dim]Auto-discovered module orchestration[/dim]")
    console.print()
    console.print("─" * 70)
    console.print()

    console.print("[bold cyan]USAGE:[/bold cyan]")
    console.print()
    console.print("  [dim]python3 speakeasy.py <command> [args...][/dim]")
    console.print("  [dim]python3 speakeasy.py --help[/dim]")
    console.print()
    console.print("─" * 70)
    console.print()

    console.print("[bold cyan]AVAILABLE COMMANDS:[/bold cyan]")
    console.print()

    if modules:
        for module in modules:
            module_name = module.__name__.split('.')[-1]
            # Get first line of docstring
            description = "No description"
            if module.__doc__:
                description = module.__doc__.strip().split('\n')[0]

            console.print(f"  [green]{module_name:20}[/green] [dim]{description}[/dim]")
    else:
        console.print("  [dim]No modules discovered[/dim]")

    console.print()
    console.print("─" * 70)
    console.print()

    console.print("[bold]TIP:[/bold] For module-specific help:")
    console.print("  [dim]python3 speakeasy.py <command> --help[/dim]")
    console.print()


# =============================================================================
# SERVICE COMMANDS (start, stop, status)
# =============================================================================

def start_service(modules: List[Any]):
    """Start Speakeasy voice-to-text service with GUI"""
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QThread, pyqtSignal
        from threading import Event
        import signal
        import time

        sys.path.insert(0, str(Path(__file__).parent))
        from handlers import (
            audio_handler, transcription_handler, hotkey_handler,
            input_handler, ui_handler, config_handler, cursor_lock_handler
        )

        # Load configuration
        config_path = Path.home() / "speakeasy" / "config.yaml"
        config = config_handler.load_config(config_path)
        logger.info("[SPEAKEASY] Configuration loaded")

        # Initialize Qt application
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        # Shared state
        model = None
        worker = None
        listener = None
        tray_icon = None
        status_window = None
        main_window = None
        settings_window = None

        # --- Recording Worker Thread ---
        class RecordingWorker(QThread):
            status_changed = pyqtSignal(str)
            text_ready = pyqtSignal(str)
            error_occurred = pyqtSignal(str)

            def __init__(self, whisper_model, cfg):
                super().__init__()
                self.model = whisper_model
                self.cfg = cfg
                self._stop_event = Event()

            def run(self):
                try:
                    if self.cfg.get("cursor_lock", {}).get("enabled", True):
                        try:
                            cursor_lock_handler.lock_cursor()
                        except Exception as lock_err:
                            logger.warning(f"[SPEAKEASY] Cursor lock failed: {lock_err}")

                    self.status_changed.emit("recording")
                    console.print("[red]Recording...[/red]")

                    rec = self.cfg.get("recording", {})
                    audio_data = audio_handler.record_audio(
                        sample_rate=rec.get("sample_rate", 16000),
                        silence_duration=rec.get("silence_duration", 900),
                        vad_aggressiveness=rec.get("vad_aggressiveness", 2),
                        min_duration=rec.get("min_duration", 100),
                        device=None,
                        stop_event=self._stop_event,
                        recording_mode=rec.get("recording_mode", "press_to_toggle")
                    )

                    if audio_data is None:
                        console.print("[yellow]Recording too short, discarded[/yellow]")
                        self.status_changed.emit("idle")
                        return

                    duration = len(audio_data) / rec.get("sample_rate", 16000)
                    console.print(f"[green]Recording complete[/green] - {duration:.1f}s, {audio_data.size} samples")

                    self.status_changed.emit("transcribing")
                    console.print("[yellow]Transcribing...[/yellow]")

                    mdl = self.cfg.get("model", {})
                    text = transcription_handler.transcribe_audio(
                        audio_data=audio_data, model=self.model,
                        language=mdl.get("language", "en"),
                        temperature=mdl.get("temperature", 0.0),
                        vad_filter=mdl.get("vad_filter", True)
                    )

                    if text and text.strip():
                        post = self.cfg.get("post_processing", {})
                        text = transcription_handler.post_process_text(
                            text=text,
                            remove_trailing_period=post.get("remove_trailing_period", False),
                            add_trailing_space=post.get("add_trailing_space", True),
                            remove_capitalization=post.get("remove_capitalization", False)
                        )
                        console.print(f"[green]Transcribed:[/green] {text.strip()}")

                        # Inject text directly (Qt signals unreliable from non-Qt thread)
                        if cursor_lock_handler.is_locked():
                            cursor_lock_handler.restore_position()
                            time.sleep(0.1)
                        inp = self.cfg.get("input", {})
                        if len(text) > inp.get("paste_threshold", 50):
                            input_handler.paste_text(text)
                        else:
                            input_handler.type_text(
                                text, method=inp.get("method", "pynput"),
                                key_delay=inp.get("key_delay", 0.005))
                        console.print("[green]Text injected[/green]")
                    else:
                        console.print("[yellow]No speech detected in recording[/yellow]")

                except Exception as e:
                    logger.error(f"[SPEAKEASY] Worker error: {e}", exc_info=True)
                    console.print(f"[red]Worker error:[/red] {e}")
                    self.error_occurred.emit(str(e))
                finally:
                    if cursor_lock_handler.is_locked():
                        cursor_lock_handler.unlock_cursor()
                    self.status_changed.emit("idle")

            def stop(self):
                self._stop_event.set()

        # --- Callbacks ---
        def on_status_change(status):
            try:
                if tray_icon:
                    ui_handler.update_tray_status(tray_icon, status)
                if status == "recording" and status_window:
                    status_window.show()
                    ui_handler.update_status_window(status_window, "recording")
                elif status == "transcribing" and status_window:
                    ui_handler.update_status_window(status_window, "transcribing")
                elif status == "idle":
                    if status_window:
                        status_window.hide()
                    if tray_icon:
                        ui_handler.update_tray_status(tray_icon, "ready")
            except Exception as e:
                logger.error(f"[SPEAKEASY] UI update error: {e}")

        def on_text_ready(text):
            nonlocal worker
            try:
                console.print(f"[cyan]Injecting text ({len(text)} chars)...[/cyan]")
                inp = config.get("input", {})
                if cursor_lock_handler.is_locked():
                    console.print("[dim]Restoring cursor position...[/dim]")
                    cursor_lock_handler.restore_position()
                    import time as _time
                    _time.sleep(0.1)
                if len(text) > inp.get("paste_threshold", 50):
                    console.print("[dim]Using paste method[/dim]")
                    input_handler.paste_text(text)
                else:
                    console.print(f"[dim]Using type method ({inp.get('method', 'pynput')})[/dim]")
                    input_handler.type_text(text, method=inp.get("method", "pynput"),
                                            key_delay=inp.get("key_delay", 0.005))
                console.print("[green]Text injected successfully[/green]")
            except Exception as e:
                console.print(f"[red]Text injection error:[/red] {e}")
                logger.error(f"[SPEAKEASY] Text injection error: {e}", exc_info=True)
            finally:
                worker = None

        def on_error(error_msg):
            nonlocal worker
            logger.error(f"[SPEAKEASY] Worker error: {error_msg}")
            worker = None

        def on_hotkey_activate():
            nonlocal worker
            if worker and worker.isRunning():
                worker.stop()
                return
            worker = RecordingWorker(model, config)
            worker.status_changed.connect(on_status_change)
            worker.text_ready.connect(on_text_ready)
            worker.error_occurred.connect(on_error)
            worker.start()

        def on_hotkey_deactivate():
            pass

        def start_hotkey_listener():
            nonlocal listener
            if listener:
                hotkey_handler.stop_listener(listener)
                listener = None
            rec = config.get("recording", {})
            key = rec.get("activation_key", "ctrl+space")
            try:
                listener = hotkey_handler.start_listener(
                    activation_key=key, on_activate=on_hotkey_activate,
                    on_deactivate=on_hotkey_deactivate, backend="auto"
                )
                logger.info(f"[SPEAKEASY] Hotkey listener started ({key})")
            except Exception as e:
                logger.error(f"[SPEAKEASY] Hotkey listener failed: {e}")

        # --- GUI Actions ---
        def on_start():
            """User clicked Start - load model and begin listening"""
            nonlocal model, tray_icon, status_window
            if main_window:
                main_window.hide()

            # Load Whisper model if not already loaded
            if model is None:
                console.print("[yellow]Loading Whisper model...[/yellow]")
                mdl_cfg = config.get("model", {})
                model = transcription_handler.create_whisper_model(
                    model_name=mdl_cfg.get("name", "base.en"),
                    device=mdl_cfg.get("device", "auto"),
                    compute_type=mdl_cfg.get("compute_type", "default")
                )
                console.print("[green]✓[/green] Whisper model loaded")

            # Create status window and tray icon
            if status_window is None:
                status_window = ui_handler.create_status_window(app)
            if tray_icon is None:
                tray_icon = ui_handler.create_tray_icon(
                    app,
                    on_show_main=lambda: main_window.show() if main_window else None,
                    on_show_settings=on_settings,
                    on_exit=on_exit
                )
            ui_handler.show_tray_icon(tray_icon)
            ui_handler.update_tray_status(tray_icon, "ready")

            # Start hotkey listener
            start_hotkey_listener()
            console.print("[green]✓[/green] Speakeasy active - press hotkey to record")

        def on_settings():
            """Show settings window"""
            nonlocal settings_window
            def save_settings(new_config):
                nonlocal config, settings_window
                config_handler.save_config(new_config, config_path)
                config = new_config
                logger.info("[SPEAKEASY] Settings saved")
                if settings_window:
                    settings_window.close()
                    settings_window = None
            def close_settings():
                nonlocal settings_window
                if settings_window:
                    settings_window.close()
                    settings_window = None
            settings_window = ui_handler.create_settings_window(
                config, on_save=save_settings, on_close=close_settings
            )
            settings_window.show()

        def on_exit():
            """Clean shutdown"""
            nonlocal worker, listener
            if worker and worker.isRunning():
                worker.stop()
                worker.wait()
            if listener:
                hotkey_handler.stop_listener(listener)
            if tray_icon:
                ui_handler.hide_tray_icon(tray_icon)
            app.quit()

        # Signal handling for Ctrl+C
        def signal_handler(_sig, _frame):
            on_exit()
        signal.signal(signal.SIGINT, signal_handler)

        # Show main window on startup
        main_window = ui_handler.create_main_window(
            app, on_start=on_start, on_settings=on_settings, on_exit=on_exit
        )
        main_window.show()

        return app.exec()

    except ImportError as e:
        console.print(f"[red]Error:[/red] Missing dependency: {e}")
        console.print("[dim]Install: PyQt5, faster-whisper, sounddevice, webrtcvad, pynput[/dim]")
        return 1
    except Exception as e:
        logger.error(f"[SPEAKEASY] Failed to start service: {e}", exc_info=True)
        console.print(f"[red]Error starting service:[/red] {e}")
        return 1


def stop_service():
    """Stop running Speakeasy service"""
    import subprocess

    console.print("[yellow]Stopping Speakeasy service...[/yellow]")

    try:
        # Find running speakeasy processes
        result = subprocess.run(
            ['pgrep', '-f', 'speakeasy.py start'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                subprocess.run(['kill', pid])
            console.print(f"[green]✓[/green] Stopped {len(pids)} process(es)")
        else:
            console.print("[dim]No running Speakeasy processes found[/dim]")

        return 0

    except Exception as e:
        logger.error(f"[SPEAKEASY] Failed to stop service: {e}")
        console.print(f"[red]Error:[/red] {e}")
        return 1


def check_status():
    """Check if Speakeasy service is running"""
    import subprocess

    try:
        result = subprocess.run(
            ['pgrep', '-f', 'speakeasy.py start'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            console.print(f"[green]✓[/green] Speakeasy is running (PID: {', '.join(pids)})")
            return 0
        else:
            console.print("[yellow]⊘[/yellow] Speakeasy is not running")
            return 1

    except Exception as e:
        logger.error(f"[SPEAKEASY] Failed to check status: {e}")
        console.print(f"[red]Error:[/red] {e}")
        return 1


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point - routes commands or shows help"""

    # Discover available modules
    modules = discover_modules()

    # Parse arguments
    args = sys.argv[1:]

    # Show introspection when run with no arguments
    if len(args) == 0:
        print_introspection(modules)
        return 0

    # Show help for explicit help flags
    if args[0] in ['--help', '-h', 'help']:
        print_help(modules)
        return 0

    # Extract command and remaining args
    command = args[0]
    remaining_args = args[1:] if len(args) > 1 else []

    # Handle service commands (start, stop, status)
    if command == "start":
        return start_service(modules)
    elif command == "stop":
        return stop_service()
    elif command == "status":
        return check_status()

    # Route to modules
    if route_command(command, remaining_args, modules):
        return 0
    else:
        console.print()
        console.print(f"[red]Unknown command: {command}[/red]")
        console.print()
        console.print("Run [dim]python3 speakeasy.py --help[/dim] for available commands")
        console.print()
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        console.print("\n\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"SPEAKEASY entry point error: {e}", exc_info=True)
        console.print(f"\n❌ Error: {e}")
        sys.exit(1)
