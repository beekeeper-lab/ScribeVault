#!/usr/bin/env python3
"""
Main entry point for ScribeVault PySide6 application.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Set environment variables for better Qt experience
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

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
        print("Error: PySide6 is not installed.")
        print("Please install PySide6 dependencies:")
        print("pip install -r requirements.txt")
        print(f"Import error: {e}")
        return 1
        
    except Exception as e:
        print(f"Application error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
