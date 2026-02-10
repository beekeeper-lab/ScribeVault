#!/usr/bin/env python3
"""
Main entry point for ScribeVault PySide6 application.
"""

import os
import sys
import logging
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Set environment variables for better Qt experience
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

# Configure logging before any other application imports
from config.logging_config import setup_logging
from config.settings import SettingsManager

_settings = SettingsManager()
setup_logging(level=getattr(_settings.settings, "log_level", "INFO"))

logger = logging.getLogger(__name__)

def main():
    """Main application entry point."""
    try:
        # Import PySide6 components
        from gui.qt_app import create_qt_application
        from gui.qt_main_window import ScribeVaultMainWindow

        # Create Qt application
        app = create_qt_application(sys.argv)

        # Create main window
        main_window = ScribeVaultMainWindow()
        app.set_main_window(main_window)

        # Show window
        main_window.show()

        # Run application
        exit_code = app.exec()

        return exit_code

    except ImportError as e:
        logger.critical("PySide6 is not installed: %s", e)
        print("Error: PySide6 is not installed.")
        print("Please install PySide6 dependencies:")
        print("pip install -r requirements.txt")
        return 1

    except Exception as e:
        logger.critical("Application error: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
