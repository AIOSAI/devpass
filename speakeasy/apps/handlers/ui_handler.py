#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: ui_handler.py - UI Components Handler
# Date: 2026-02-11
# Version: 2.0.0
# Category: speakeasy/handlers
#
# CHANGELOG (Max 5 entries):
#   - v2.0.0 (2026-02-11): Complete GUI implementation with base, main, settings, status windows
#   - v1.0.0 (2026-02-11): Initial placeholder implementation
#
# CODE STANDARDS:
#   - Handlers implement logic, modules orchestrate
#   - Pure functions only - no classes except minimal UI helpers
#   - Handlers are internal - imported by modules only
# =============================================

"""UI Handler - Pure functions for GUI windows and components.

Provides:
- Base window class (frameless, draggable, rounded)
- Main window (Start/Settings buttons)
- Settings window (tabbed config editor)
- Status window (bottom-center recording/transcribing indicator)
- System tray icon with status colors

All window creation functions return QWidget instances configured and ready to use.
"""

from PyQt5.QtCore import Qt, QRectF, pyqtSignal, QEvent
from PyQt5.QtGui import (
    QPainter, QBrush, QColor, QFont, QPainterPath, QGuiApplication,
    QIcon, QPixmap
)
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QSystemTrayIcon, QMenu, QAction, QTabWidget, QComboBox, QLineEdit,
    QCheckBox, QSpinBox, QDoubleSpinBox, QMessageBox, QApplication,
    QScrollArea
)


# ============================================================================
# ICON GENERATION (No external files needed)
# ============================================================================

def create_colored_icon(color, size=64):
    """Create a simple colored circle icon programmatically.

    Args:
        color: Color string (e.g., 'green', 'red', 'orange') or QColor
        size: Icon size in pixels

    Returns:
        QIcon with colored circle
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # Parse color
    if isinstance(color, str):
        color_map = {
            'green': QColor(46, 204, 113),
            'red': QColor(231, 76, 60),
            'orange': QColor(243, 156, 18),
            'blue': QColor(52, 152, 219),
        }
        qcolor = color_map.get(color, QColor(color))
    else:
        qcolor = color

    painter.setBrush(qcolor)
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(4, 4, size - 8, size - 8)
    painter.end()

    return QIcon(pixmap)


def create_status_pixmap(symbol, color, size=32):
    """Create a status indicator pixmap with symbol.

    Args:
        symbol: Unicode symbol (e.g., '🎤', '✍️', '✓')
        color: Background color
        size: Icon size

    Returns:
        QPixmap with symbol on colored background
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # Draw background circle
    painter.setBrush(QColor(color))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, size, size)

    # Draw symbol
    painter.setPen(QColor(255, 255, 255))
    painter.setFont(QFont('Sans', size // 2))
    painter.drawText(0, 0, size, size, Qt.AlignCenter, symbol)
    painter.end()

    return pixmap


# ============================================================================
# BASE WINDOW CLASS (Minimal helper for frameless draggable windows)
# ============================================================================

class BaseWindow(QMainWindow):
    """Frameless, translucent, draggable base window with rounded corners.

    This is a minimal helper class for UI implementation - not a handler violation
    since it's an internal implementation detail returned by handler functions.
    """

    def __init__(self, title, width, height):
        super().__init__()
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(width, height)

        self.is_dragging = False
        self.start_position = None

        # Main widget and layout
        self.main_widget = QWidget(self)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # Title bar with close button
        self._create_title_bar(title)

        self.setCentralWidget(self.main_widget)
        self._center_on_screen()

    def _create_title_bar(self, title):
        """Create title bar with centered title and close button."""
        title_bar = QWidget()
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)

        # Title label
        title_label = QLabel(title)
        title_label.setFont(QFont('Segoe UI', 12, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #404040;")

        # Close button
        close_button = QPushButton('×')
        close_button.setFixedSize(25, 25)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #404040;
                font-size: 20px;
            }
            QPushButton:hover {
                color: #000000;
            }
        """)
        close_button.clicked.connect(self.close)

        # Layout: left spacer, title, close button
        title_bar_layout.addWidget(QWidget(), 1)
        title_bar_layout.addWidget(title_label, 3)
        title_bar_layout.addWidget(close_button, alignment=Qt.AlignRight)

        self.main_layout.addWidget(title_bar)

    def _center_on_screen(self):
        """Center window on primary screen."""
        center_point = QGuiApplication.primaryScreen().availableGeometry().center()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    def mousePressEvent(self, event):
        """Start dragging window."""
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.start_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Move window while dragging."""
        if self.is_dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.start_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Stop dragging window."""
        self.is_dragging = False

    def paintEvent(self, event):
        """Paint rounded semi-transparent background."""
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 20, 20)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(255, 255, 255, 220)))
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)


# ============================================================================
# MAIN WINDOW
# ============================================================================

def create_main_window(app, on_start, on_settings, on_exit):
    """Create the main control window (Start/Settings buttons).

    Args:
        app: QApplication instance
        on_start: Callback for Start button (called when clicked, window auto-hides)
        on_settings: Callback for Settings button
        on_exit: Callback for window close

    Returns:
        BaseWindow configured as main window
    """
    window = BaseWindow('Speakeasy', 320, 180)

    # Override close event to call on_exit
    def close_handler(event):
        on_exit()
        event.accept()
    window.closeEvent = close_handler

    # Start button
    start_btn = QPushButton('Start')
    start_btn.setFont(QFont('Segoe UI', 10))
    start_btn.setFixedSize(120, 60)
    start_btn.setStyleSheet("""
        QPushButton {
            background-color: #2ecc71;
            color: white;
            border: none;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #27ae60;
        }
    """)

    def start_clicked():
        on_start()
        window.hide()
    start_btn.clicked.connect(start_clicked)

    # Settings button
    settings_btn = QPushButton('Settings')
    settings_btn.setFont(QFont('Segoe UI', 10))
    settings_btn.setFixedSize(120, 60)
    settings_btn.setStyleSheet("""
        QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #2980b9;
        }
    """)
    settings_btn.clicked.connect(on_settings)

    # Button layout
    button_layout = QHBoxLayout()
    button_layout.addStretch(1)
    button_layout.addWidget(start_btn)
    button_layout.addWidget(settings_btn)
    button_layout.addStretch(1)

    window.main_layout.addStretch(1)
    window.main_layout.addLayout(button_layout)
    window.main_layout.addStretch(1)

    return window


# ============================================================================
# SETTINGS WINDOW
# ============================================================================

def create_settings_window(config, on_save, on_close):
    """Create the settings configuration window.

    Args:
        config: Current configuration dict (from config_handler.load_config)
        on_save: Callback(new_config) when Save button clicked
        on_close: Callback when window closed without saving

    Returns:
        BaseWindow configured as settings window
    """
    window = BaseWindow('Settings', 700, 700)

    # Tab widget
    tabs = QTabWidget()
    window.main_layout.addWidget(tabs)

    # Storage for widgets to read values later
    widgets = {}

    # Create tabs for each config section
    section_titles = {
        'model': 'Model',
        'recording': 'Recording',
        'input': 'Input',
        'post_processing': 'Post Processing',
        'cursor_lock': 'Cursor Lock',
        'ui': 'UI'
    }

    for section_key, section_title in section_titles.items():
        if section_key not in config:
            continue

        tab = QWidget()
        tab_layout = QVBoxLayout()

        # Scroll area for tab content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Add setting widgets for this section
        for key, value in config[section_key].items():
            setting_layout = QHBoxLayout()

            # Label
            label = QLabel(key.replace('_', ' ').title() + ':')
            label.setFixedWidth(200)
            setting_layout.addWidget(label)

            # Widget based on value type
            widget = None
            if isinstance(value, bool):
                widget = QCheckBox()
                widget.setChecked(value)
            elif isinstance(value, int):
                widget = QSpinBox()
                widget.setRange(0, 999999)
                widget.setValue(value)
            elif isinstance(value, float):
                widget = QDoubleSpinBox()
                widget.setRange(0.0, 999999.0)
                widget.setSingleStep(0.1)
                widget.setValue(value)
            elif isinstance(value, str):
                # Check for common dropdowns
                if key == 'name':  # model name
                    widget = QComboBox()
                    widget.addItems(['tiny', 'tiny.en', 'base', 'base.en', 'small',
                                    'small.en', 'medium', 'medium.en', 'large'])
                    widget.setCurrentText(value)
                elif key == 'device':
                    widget = QComboBox()
                    widget.addItems(['auto', 'cuda', 'cpu'])
                    widget.setCurrentText(value)
                elif key == 'compute_type':
                    widget = QComboBox()
                    widget.addItems(['default', 'float32', 'float16', 'int8'])
                    widget.setCurrentText(value)
                elif key == 'recording_mode':
                    widget = QComboBox()
                    widget.addItems(['continuous', 'voice_activity_detection',
                                    'press_to_toggle', 'hold_to_record'])
                    widget.setCurrentText(value)
                elif key == 'method':  # input method
                    widget = QComboBox()
                    widget.addItems(['pynput', 'ydotool', 'dotool'])
                    widget.setCurrentText(value)
                else:
                    widget = QLineEdit(str(value))

            if widget:
                setting_layout.addWidget(widget)
                widgets[f"{section_key}.{key}"] = widget

            scroll_layout.addLayout(setting_layout)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)

        tab_layout.addWidget(scroll)
        tab.setLayout(tab_layout)
        tabs.addTab(tab, section_title)

    # Buttons
    button_layout = QHBoxLayout()

    reset_btn = QPushButton('Reset to Current')
    reset_btn.clicked.connect(lambda: _reset_settings_widgets(widgets, config))
    button_layout.addWidget(reset_btn)

    button_layout.addStretch()

    save_btn = QPushButton('Save')
    save_btn.setStyleSheet("""
        QPushButton {
            background-color: #2ecc71;
            color: white;
            padding: 8px 24px;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #27ae60;
        }
    """)

    def save_clicked():
        new_config = _read_settings_widgets(widgets, config)
        on_save(new_config)
        QMessageBox.information(window, 'Settings Saved',
                               'Settings have been saved successfully.')
        window.close()

    save_btn.clicked.connect(save_clicked)
    button_layout.addWidget(save_btn)

    window.main_layout.addLayout(button_layout)

    # Close without saving confirmation
    def close_handler(event):
        reply = QMessageBox.question(
            window,
            'Close Without Saving?',
            'Are you sure you want to close without saving changes?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            on_close()
            event.accept()
        else:
            event.ignore()

    window.closeEvent = close_handler

    return window


def _read_settings_widgets(widgets, original_config):
    """Read values from settings widgets and return new config dict."""
    new_config = {}

    for key, widget in widgets.items():
        section, setting = key.split('.', 1)

        if section not in new_config:
            new_config[section] = {}

        # Read value based on widget type
        if isinstance(widget, QCheckBox):
            value = widget.isChecked()
        elif isinstance(widget, QSpinBox):
            value = widget.value()
        elif isinstance(widget, QDoubleSpinBox):
            value = widget.value()
        elif isinstance(widget, QComboBox):
            value = widget.currentText()
        elif isinstance(widget, QLineEdit):
            value = widget.text()
        else:
            continue

        new_config[section][setting] = value

    # Merge with original to preserve any sections not in widgets
    for section in original_config:
        if section not in new_config:
            new_config[section] = original_config[section].copy()

    return new_config


def _reset_settings_widgets(widgets, config):
    """Reset all widgets to current config values."""
    for key, widget in widgets.items():
        section, setting = key.split('.', 1)
        value = config.get(section, {}).get(setting)

        if value is None:
            continue

        if isinstance(widget, QCheckBox):
            widget.setChecked(value)
        elif isinstance(widget, QSpinBox):
            widget.setValue(value)
        elif isinstance(widget, QDoubleSpinBox):
            widget.setValue(value)
        elif isinstance(widget, QComboBox):
            widget.setCurrentText(str(value))
        elif isinstance(widget, QLineEdit):
            widget.setText(str(value))


# ============================================================================
# STATUS WINDOW
# ============================================================================

def create_status_window(app):
    """Create the bottom-center status indicator window.

    Args:
        app: QApplication instance

    Returns:
        QWidget configured as status window (hidden initially)
    """
    window = QWidget()
    window.setWindowFlags(
        Qt.FramelessWindowHint |
        Qt.WindowStaysOnTopHint |
        Qt.Tool
    )
    window.setAttribute(Qt.WA_TranslucentBackground)
    window.setFixedSize(320, 120)

    # Background
    window.setStyleSheet("""
        QWidget {
            background-color: rgba(50, 50, 50, 230);
            border-radius: 15px;
        }
    """)

    # Layout
    layout = QHBoxLayout()
    layout.setContentsMargins(20, 20, 20, 20)

    # Icon label
    icon_label = QLabel()
    icon_label.setFixedSize(64, 64)
    icon_label.setAlignment(Qt.AlignCenter)

    # Text label
    text_label = QLabel('Ready')
    text_label.setFont(QFont('Segoe UI', 16, QFont.Bold))
    text_label.setStyleSheet("color: white;")
    text_label.setAlignment(Qt.AlignCenter)

    layout.addWidget(icon_label)
    layout.addWidget(text_label)

    window.setLayout(layout)

    # Store references for updates
    window.icon_label = icon_label
    window.text_label = text_label

    return window


def update_status_window(window, status, text=""):
    """Update status window and show/hide it.

    Args:
        window: Status window from create_status_window()
        status: Status string ('recording', 'transcribing', 'idle')
        text: Optional custom text (default uses status-based text)
    """
    if not hasattr(window, 'icon_label') or not hasattr(window, 'text_label'):
        return

    # Status config
    status_config = {
        'recording': {
            'icon': '🎤',
            'color': '#e74c3c',
            'text': 'Recording...'
        },
        'transcribing': {
            'icon': '✍️',
            'color': '#f39c12',
            'text': 'Transcribing...'
        },
        'idle': {
            'icon': '✓',
            'color': '#2ecc71',
            'text': 'Ready'
        }
    }

    config = status_config.get(status, status_config['idle'])

    # Update icon
    pixmap = create_status_pixmap(config['icon'], config['color'], 64)
    window.icon_label.setPixmap(pixmap)

    # Update text
    window.text_label.setText(text if text else config['text'])

    # Show for recording/transcribing, hide for idle
    if status in ('recording', 'transcribing'):
        if not window.isVisible():
            # Position at bottom-center
            screen = QApplication.primaryScreen()
            screen_geometry = screen.geometry()
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()

            x = (screen_width - window.width()) // 2
            y = screen_height - window.height() - 120

            window.move(x, y)
            window.show()
    else:
        window.hide()


# ============================================================================
# SYSTEM TRAY ICON
# ============================================================================

def create_tray_icon(app, on_show_main, on_show_settings, on_exit):
    """Create system tray icon with menu.

    Args:
        app: QApplication instance
        on_show_main: Callback to show main window
        on_show_settings: Callback to show settings window
        on_exit: Callback to exit application

    Returns:
        QSystemTrayIcon instance
    """
    # Create with default green icon
    icon = create_colored_icon('green', 64)
    tray = QSystemTrayIcon(icon, app)

    # Create menu
    menu = QMenu()

    show_action = QAction('Show Window', app)
    show_action.triggered.connect(on_show_main)
    menu.addAction(show_action)

    settings_action = QAction('Settings', app)
    settings_action.triggered.connect(on_show_settings)
    menu.addAction(settings_action)

    menu.addSeparator()

    exit_action = QAction('Exit', app)
    exit_action.triggered.connect(on_exit)
    menu.addAction(exit_action)

    tray.setContextMenu(menu)
    tray.setToolTip('Speakeasy - Ready')

    return tray


def update_tray_status(tray, status):
    """Update tray icon color and tooltip based on status.

    Args:
        tray: QSystemTrayIcon instance
        status: Status string ('ready', 'locked', 'processing')
    """
    status_config = {
        'ready': ('green', 'Speakeasy - Ready'),
        'locked': ('red', 'Speakeasy - Cursor Locked'),
        'processing': ('orange', 'Speakeasy - Processing...'),
        'recording': ('orange', 'Speakeasy - Recording...'),
    }

    color, tooltip = status_config.get(status, ('green', 'Speakeasy'))

    icon = create_colored_icon(color, 64)
    tray.setIcon(icon)
    tray.setToolTip(tooltip)


def show_tray_icon(tray):
    """Show the tray icon."""
    tray.show()


def hide_tray_icon(tray):
    """Hide the tray icon."""
    tray.hide()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_base_window(title, width, height):
    """Create a basic frameless window (used by custom window builders).

    Args:
        title: Window title
        width: Window width in pixels
        height: Window height in pixels

    Returns:
        BaseWindow instance
    """
    return BaseWindow(title, width, height)
