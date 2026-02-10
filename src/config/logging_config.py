"""
Centralized logging configuration for ScribeVault.

Call setup_logging() once from the application entry point (main.py or main_qt.py)
before any other imports that use logging. Individual modules should only use:

    import logging
    logger = logging.getLogger(__name__)
"""

import logging
import sys
from pathlib import Path


def setup_logging(level: str = "INFO", log_file: str = "scribevault.log"):
    """Configure the root logger with console and file handlers.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Path to the log file. Relative paths are resolved from cwd.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    root_logger = logging.getLogger()

    # Idempotent: remove existing handlers to avoid duplicates on repeated calls
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()

    root_logger.setLevel(numeric_level)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler
    try:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(log_path), encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except OSError:
        root_logger.warning("Could not create log file at %s", log_file)
