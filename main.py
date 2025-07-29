#!/usr/bin/env python3
"""
ScribeVault - Audio Recording, Transcription, and AI Summarization Tool

A modern GUI application for capturing, transcribing, and organizing audio content.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Now import the main application
from gui.main_window import ScribeVaultApp

def main():
    """Main entry point for ScribeVault application."""
    try:
        app = ScribeVaultApp()
        app.run()
    except KeyboardInterrupt:
        print("\nScribeVault terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting ScribeVault: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
