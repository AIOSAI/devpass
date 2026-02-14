#!/home/aipass/.venv/bin/python3
"""Quick test of UI components - DO NOT COMMIT"""

import sys
sys.path.insert(0, 'apps/handlers')

from PyQt5.QtWidgets import QApplication
import ui_handler

def test_main_window():
    """Test main window creation."""
    app = QApplication(sys.argv)

    def on_start():
        print("Start clicked!")

    def on_settings():
        print("Settings clicked!")

    def on_exit():
        print("Exit clicked!")
        app.quit()

    main_win = ui_handler.create_main_window(app, on_start, on_settings, on_exit)
    main_win.show()

    sys.exit(app.exec_())

def test_settings_window():
    """Test settings window creation."""
    app = QApplication(sys.argv)

    config = {
        'model': {'name': 'base.en', 'device': 'auto', 'compute_type': 'default'},
        'recording': {'activation_key': 'ctrl+space', 'recording_mode': 'press_to_toggle', 'sample_rate': 16000},
        'input': {'method': 'pynput', 'key_delay': 0.005},
        'cursor_lock': {'enabled': True}
    }

    def on_save(new_config):
        print("Config saved:", new_config)

    def on_close():
        print("Settings closed without saving")

    settings_win = ui_handler.create_settings_window(config, on_save, on_close)
    settings_win.show()

    sys.exit(app.exec_())

def test_status_window():
    """Test status window."""
    from PyQt5.QtCore import QTimer
    app = QApplication(sys.argv)

    status_win = ui_handler.create_status_window(app)

    # Show recording status
    ui_handler.update_status_window(status_win, 'recording')

    # Change to transcribing after 3 seconds
    QTimer.singleShot(3000, lambda: ui_handler.update_status_window(status_win, 'transcribing'))

    # Hide after 6 seconds
    QTimer.singleShot(6000, lambda: ui_handler.update_status_window(status_win, 'idle'))

    # Exit after 7 seconds
    QTimer.singleShot(7000, app.quit)

    sys.exit(app.exec_())

def test_tray_icon():
    """Test system tray icon."""
    app = QApplication(sys.argv)

    def on_show():
        print("Show main window")

    def on_settings():
        print("Show settings")

    def on_exit():
        print("Exit")
        app.quit()

    tray = ui_handler.create_tray_icon(app, on_show, on_settings, on_exit)
    ui_handler.show_tray_icon(tray)

    # Change colors every 2 seconds
    from PyQt5.QtCore import QTimer
    timer = QTimer()
    statuses = ['ready', 'recording', 'processing', 'locked']
    counter = [0]

    def cycle_status():
        status = statuses[counter[0] % len(statuses)]
        ui_handler.update_tray_status(tray, status)
        print(f"Status: {status}")
        counter[0] += 1

    timer.timeout.connect(cycle_status)
    timer.start(2000)

    print("Tray icon running. Right-click to see menu. Will cycle colors every 2 seconds.")
    sys.exit(app.exec_())

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        test = sys.argv[1]
        if test == 'main':
            test_main_window()
        elif test == 'settings':
            test_settings_window()
        elif test == 'status':
            test_status_window()
        elif test == 'tray':
            test_tray_icon()
        else:
            print(f"Unknown test: {test}")
            print("Usage: python3 test_ui.py [main|settings|status|tray]")
    else:
        print("Usage: python3 test_ui.py [main|settings|status|tray]")
        print("\nAvailable tests:")
        print("  main     - Test main window (Start/Settings buttons)")
        print("  settings - Test settings configuration window")
        print("  status   - Test status indicator window")
        print("  tray     - Test system tray icon")
