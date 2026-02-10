"""
Unit tests for centralized logging configuration.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import logging
import tempfile
import unittest

from config.logging_config import setup_logging


class TestSetupLogging(unittest.TestCase):
    """Test cases for setup_logging function."""

    def setUp(self):
        """Reset the root logger before each test."""
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)
            handler.close()
        root.setLevel(logging.WARNING)  # default level

    def tearDown(self):
        """Clean up handlers after each test."""
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)
            handler.close()

    def test_configures_console_handler(self):
        """setup_logging adds a StreamHandler."""
        setup_logging(level="INFO", log_file=os.devnull)
        root = logging.getLogger()
        stream_handlers = [
            h for h in root.handlers if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)
        ]
        self.assertEqual(len(stream_handlers), 1)

    def test_configures_file_handler(self):
        """setup_logging adds a FileHandler writing to the specified file."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            log_path = f.name
        try:
            setup_logging(level="DEBUG", log_file=log_path)
            root = logging.getLogger()
            file_handlers = [
                h for h in root.handlers if isinstance(h, logging.FileHandler)
            ]
            self.assertEqual(len(file_handlers), 1)

            # Write a message and verify it appears in the file
            test_logger = logging.getLogger("test.file_handler")
            test_logger.info("file handler test message")

            # Flush handlers
            for h in root.handlers:
                h.flush()

            with open(log_path, "r") as lf:
                content = lf.read()
            self.assertIn("file handler test message", content)
        finally:
            os.unlink(log_path)

    def test_sets_log_level(self):
        """setup_logging correctly sets the root logger level."""
        setup_logging(level="DEBUG", log_file=os.devnull)
        self.assertEqual(logging.getLogger().level, logging.DEBUG)

        setup_logging(level="WARNING", log_file=os.devnull)
        self.assertEqual(logging.getLogger().level, logging.WARNING)

    def test_idempotent_no_duplicate_handlers(self):
        """Calling setup_logging multiple times does not duplicate handlers."""
        setup_logging(level="INFO", log_file=os.devnull)
        setup_logging(level="INFO", log_file=os.devnull)
        setup_logging(level="INFO", log_file=os.devnull)

        root = logging.getLogger()
        # Should have exactly 2 handlers: one StreamHandler + one FileHandler
        # (FileHandler to /dev/null)
        self.assertEqual(len(root.handlers), 2)

    def test_log_format_contains_expected_fields(self):
        """Log output includes timestamp, level, logger name, and message."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            log_path = f.name
        try:
            setup_logging(level="INFO", log_file=log_path)

            test_logger = logging.getLogger("mymodule.test")
            test_logger.info("format check message")

            for h in logging.getLogger().handlers:
                h.flush()

            with open(log_path, "r") as lf:
                content = lf.read()

            # Check for expected format fields
            self.assertIn("[INFO    ]", content)
            self.assertIn("mymodule.test", content)
            self.assertIn("format check message", content)
        finally:
            os.unlink(log_path)

    def test_level_filtering(self):
        """Messages below the configured level are filtered out."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            log_path = f.name
        try:
            setup_logging(level="WARNING", log_file=log_path)

            test_logger = logging.getLogger("filter.test")
            test_logger.debug("should not appear")
            test_logger.info("should not appear either")
            test_logger.warning("should appear")

            for h in logging.getLogger().handlers:
                h.flush()

            with open(log_path, "r") as lf:
                content = lf.read()

            self.assertNotIn("should not appear", content)
            self.assertIn("should appear", content)
        finally:
            os.unlink(log_path)

    def test_invalid_log_file_path_does_not_crash(self):
        """setup_logging gracefully handles an unwritable log file path."""
        # Use an invalid path that cannot be created
        setup_logging(level="INFO", log_file="/nonexistent/dir/deep/nested/test.log")
        root = logging.getLogger()
        # Should still have at least the console handler
        stream_handlers = [
            h for h in root.handlers if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)
        ]
        self.assertGreaterEqual(len(stream_handlers), 1)

    def test_default_level_is_info(self):
        """Default log level is INFO when called with defaults."""
        setup_logging(log_file=os.devnull)
        self.assertEqual(logging.getLogger().level, logging.INFO)


class TestAppSettingsLogLevel(unittest.TestCase):
    """Test that AppSettings includes log_level field."""

    def test_app_settings_has_log_level(self):
        """AppSettings dataclass has a log_level field defaulting to INFO."""
        from config.settings import AppSettings, TranscriptionSettings, SummarizationSettings, UISettings

        settings = AppSettings(
            transcription=TranscriptionSettings(),
            summarization=SummarizationSettings(),
            ui=UISettings(),
        )
        self.assertEqual(settings.log_level, "INFO")

    def test_app_settings_custom_log_level(self):
        """AppSettings accepts a custom log_level."""
        from config.settings import AppSettings, TranscriptionSettings, SummarizationSettings, UISettings

        settings = AppSettings(
            transcription=TranscriptionSettings(),
            summarization=SummarizationSettings(),
            ui=UISettings(),
            log_level="DEBUG",
        )
        self.assertEqual(settings.log_level, "DEBUG")


if __name__ == "__main__":
    unittest.main()
