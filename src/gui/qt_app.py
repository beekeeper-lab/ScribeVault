"""
Base PySide6 application class for ScribeVault.
"""

import sys
from typing import Optional
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon
from PySide6.QtCore import QSettings, QTimer, Signal, QThread
from PySide6.QtGui import QIcon, QFont, QPalette, QAction
import qdarkstyle

from config.settings import SettingsManager
from audio.recorder import AudioRecorder
from transcription.whisper_service import WhisperService
from ai.summarizer import SummarizerService
from vault.manager import VaultManager


class ScribeVaultQtApp(QApplication):
    """
    Main Qt Application class with theme management and system integration.
    """
    
    def __init__(self, argv: list):
        super().__init__(argv)
        
        # Application metadata
        self.setApplicationName("ScribeVault")
        self.setApplicationVersion("2.0.0")
        self.setApplicationDisplayName("ScribeVault")
        self.setOrganizationName("Beekeeper Lab")
        self.setOrganizationDomain("beekeeper-lab.com")
        
        # Initialize settings
        self.settings = QSettings()
        
        # Setup application
        self.setup_theme()
        self.setup_fonts()
        self.setup_system_tray()
        
        # Application state
        self.main_window: Optional[QMainWindow] = None
        
    def setup_theme(self):
        """Setup application theme and styling."""
        # Load theme preference
        theme = self.settings.value("ui/theme", "dark")
        
        if theme == "dark":
            self.setStyleSheet(qdarkstyle.load_stylesheet_pyside6())
        elif theme == "light":
            # qdarkstyle doesn't have light theme, use default
            self.setStyleSheet("")
        else:
            # Auto theme - default to dark
            self.setStyleSheet(qdarkstyle.load_stylesheet_pyside6())
            
        # Custom ScribeVault styling
        custom_styles = """
        /* ScribeVault Custom Styles */
        
        .RecordButton {
            QPushButton {
                background-color: #1f538d;
                border: 2px solid #164a7b;
                border-radius: 8px;
                color: white;
                font-weight: bold;
                padding: 12px 20px;
                font-size: 14px;
            }
            
            QPushButton:hover {
                background-color: #164a7b;
                border-color: #0f3a5f;
            }
            
            QPushButton:pressed {
                background-color: #0f3a5f;
            }
            
            QPushButton:disabled {
                background-color: #666666;
                border-color: #555555;
                color: #999999;
            }
        }
        
        .RecordButton[recording="true"] {
            QPushButton {
                background-color: #d32f2f;
                border-color: #b71c1c;
                animation: pulse 2s infinite;
            }
            
            QPushButton:hover {
                background-color: #b71c1c;
                border-color: #8f0000;
            }
        }
        
        .VaultButton, .SettingsButton {
            QPushButton {
                background-color: #666666;
                border: 2px solid #555555;
                border-radius: 8px;
                color: white;
                padding: 12px 16px;
                font-size: 14px;
            }
            
            QPushButton:hover {
                background-color: #555555;
                border-color: #444444;
            }
        }
        
        .MarkdownButton {
            QPushButton {
                background-color: #6b46c1;
                border: 2px solid #553c9a;
                border-radius: 8px;
                color: white;
                font-weight: bold;
                padding: 12px 16px;
                font-size: 14px;
            }
            
            QPushButton:hover {
                background-color: #553c9a;
                border-color: #4c1d95;
            }
        }
        
        .StatusFrame {
            QFrame {
                background-color: rgba(42, 42, 42, 0.8);
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px;
            }
        }
        
        .TranscriptArea, .SummaryArea {
            QTextEdit {
                background-color: #f5f5f5;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 8px;
                padding: 12px;
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 13px;
                line-height: 1.4;
            }
        }
        
        .TranscriptArea[theme="dark"], .SummaryArea[theme="dark"] {
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border-color: #555555;
            }
        }
        
        /* Header styling */
        .HeaderFrame {
            QFrame {
                background-color: #2a2a2a;
                border: none;
                border-radius: 0px;
            }
            
            QLabel {
                color: white;
                font-size: 32px;
                font-weight: bold;
            }
        }
        
        /* Recording cards in vault */
        .RecordingCard {
            QFrame {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 12px;
                margin: 4px;
            }
            
            QFrame:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-color: rgba(255, 255, 255, 0.2);
            }
        }
        
        /* Dialog styling */
        QDialog {
            background-color: #1e1e1e;
            color: white;
        }
        
        QDialog QFrame {
            background-color: transparent;
        }
        
        /* Scrollbars */
        QScrollBar:vertical {
            background-color: #2b2b2b;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #555555;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #666666;
        }
        
        /* Progress bars */
        QProgressBar {
            border: 1px solid #555555;
            border-radius: 4px;
            text-align: center;
            background-color: #2b2b2b;
            color: white;
        }
        
        QProgressBar::chunk {
            background-color: #1f538d;
            border-radius: 3px;
        }
        """
        
        # Apply custom styles
        current_stylesheet = self.styleSheet()
        self.setStyleSheet(current_stylesheet + custom_styles)
        
    def setup_fonts(self):
        """Setup application fonts."""
        # Load custom fonts if available
        font_path = Path("src/assets/fonts")
        if font_path.exists():
            for font_file in font_path.glob("*.ttf"):
                self.addApplicationFont(str(font_file))
        
        # Set default application font
        font = QFont("Segoe UI", 10)
        self.setFont(font)
        
    def setup_system_tray(self):
        """Setup system tray integration."""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            
            # Set tray icon
            icon_path = Path("src/assets/icons/app_icon.png")
            if icon_path.exists():
                self.tray_icon.setIcon(QIcon(str(icon_path)))
            else:
                # Use default icon
                self.tray_icon.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
            
            # Create tray menu
            from PySide6.QtWidgets import QMenu
            tray_menu = QMenu()
            
            show_action = QAction("Show ScribeVault", self)
            show_action.triggered.connect(self.show_main_window)
            tray_menu.addAction(show_action)
            
            tray_menu.addSeparator()
            
            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(self.quit)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self.tray_icon_activated)
            
            # Show tray icon
            self.tray_icon.show()
            
    def tray_icon_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_main_window()
            
    def show_main_window(self):
        """Show and raise the main window."""
        if self.main_window:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
            
    def set_main_window(self, window: QMainWindow):
        """Set the main application window."""
        self.main_window = window
        
    def change_theme(self, theme: str):
        """Change application theme."""
        self.settings.setValue("ui/theme", theme)
        
        # Apply new theme
        if theme == "dark":
            self.setStyleSheet(qdarkstyle.load_stylesheet_pyside6())
        elif theme == "light":
            # qdarkstyle doesn't have light theme, use default
            self.setStyleSheet("")
        else:
            self.setStyleSheet(qdarkstyle.load_stylesheet_pyside6())
            
        # Reapply custom styles
        self.setup_theme()
        
    def get_theme(self) -> str:
        """Get current theme setting."""
        return self.settings.value("ui/theme", "dark")


class ScribeVaultWorker(QThread):
    """
    Base worker thread class for background operations.
    """
    
    # Signals
    finished = Signal(object)  # Success signal with result
    error = Signal(str)        # Error signal with message
    progress = Signal(int)     # Progress signal (0-100)
    status = Signal(str)       # Status message signal
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_cancelled = False
        
    def cancel(self):
        """Cancel the worker operation."""
        self._is_cancelled = True
        
    def is_cancelled(self) -> bool:
        """Check if operation was cancelled."""
        return self._is_cancelled
        
    def emit_progress(self, value: int, message: str = ""):
        """Emit progress update."""
        if not self._is_cancelled:
            self.progress.emit(value)
            if message:
                self.status.emit(message)
                
    def emit_status(self, message: str):
        """Emit status update."""
        if not self._is_cancelled:
            self.status.emit(message)
            
    def run(self):
        """Override this method in subclasses."""
        raise NotImplementedError("Subclasses must implement run()")


def create_qt_application(argv: list):
    """
    Create and configure the Qt application.
    
    Args:
        argv: Command line arguments
        
    Returns:
        Configured ScribeVaultQtApp instance
    """
    # High DPI support is enabled by default in Qt 6
    
    # Create application
    app = ScribeVaultQtApp(argv)
    
    # Set application icon
    icon_path = Path("src/assets/icons/app_icon.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    return app
