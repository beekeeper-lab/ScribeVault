#!/usr/bin/env python3
"""
ScribeVault - Audio Recording, Transcription, and AI Summarization Tool

A modern GUI application for capturing, transcribing, and organizing audio content.
"""

import sys
import logging
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Configure logging before any other application imports
from config.logging_config import setup_logging
from config.settings import SettingsManager

_settings = SettingsManager()
setup_logging(level=getattr(_settings.settings, "log_level", "INFO"))

logger = logging.getLogger(__name__)

# Now import the main application
from gui.main_window import ScribeVaultApp

def main():
    """Main entry point for ScribeVault application."""
    try:
        app = ScribeVaultApp()
        app.run()
    except KeyboardInterrupt:
        logger.info("ScribeVault terminated by user.")
        sys.exit(0)
    except Exception as e:
        logger.critical("Error starting ScribeVault: %s", e, exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
