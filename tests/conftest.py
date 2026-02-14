"""
Shared pytest fixtures and configuration for ScribeVault tests.

Handles pyaudio mocking for headless/CI environments and
QT_QPA_PLATFORM for GUI tests.
"""

import os
import sys
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# PyAudio mock — injected *before* any test module imports audio.recorder
# ---------------------------------------------------------------------------

def _install_pyaudio_mock():
    """Install a pyaudio mock into sys.modules if pyaudio is not available."""
    if "pyaudio" not in sys.modules:
        try:
            import pyaudio  # noqa: F401
        except ImportError:
            mock_pyaudio = MagicMock()
            mock_pyaudio.paInt16 = 8
            mock_pyaudio.paContinue = 0
            sys.modules["pyaudio"] = mock_pyaudio


_install_pyaudio_mock()


# ---------------------------------------------------------------------------
# QT offscreen platform — prevent segfaults when no display server exists
# ---------------------------------------------------------------------------

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
