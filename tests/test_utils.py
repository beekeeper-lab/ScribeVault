"""
Unit tests for shared utility functions in src/utils.py.
"""

import os
import sys
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils import (  # noqa: E402
    format_duration, format_file_size, parse_datetime, open_with_system_app,
)


class TestFormatDurationCompact(unittest.TestCase):
    """Tests for format_duration with compact (M:SS) style."""

    def test_zero(self):
        self.assertEqual(format_duration(0), "0:00")

    def test_negative(self):
        self.assertEqual(format_duration(-5), "0:00")

    def test_none(self):
        self.assertEqual(format_duration(None), "0:00")

    def test_seconds_only(self):
        self.assertEqual(format_duration(45), "0:45")

    def test_minutes_and_seconds(self):
        self.assertEqual(format_duration(125), "2:05")

    def test_exact_minute(self):
        self.assertEqual(format_duration(60), "1:00")

    def test_over_an_hour(self):
        self.assertEqual(format_duration(3661), "61:01")

    def test_float_seconds(self):
        self.assertEqual(format_duration(90.7), "1:30")


class TestFormatDurationDescriptive(unittest.TestCase):
    """Tests for format_duration with descriptive (Xh Xm Xs) style."""

    def test_zero(self):
        self.assertEqual(format_duration(0, style="descriptive"), "Unknown")

    def test_negative(self):
        self.assertEqual(format_duration(-1, style="descriptive"), "Unknown")

    def test_none(self):
        self.assertEqual(format_duration(None, style="descriptive"), "Unknown")

    def test_seconds_only(self):
        self.assertEqual(format_duration(30, style="descriptive"), "30s")

    def test_minutes_and_seconds(self):
        self.assertEqual(format_duration(325.5, style="descriptive"), "5m 25s")

    def test_hours_minutes_seconds(self):
        self.assertEqual(
            format_duration(3661, style="descriptive"), "1h 1m 1s"
        )

    def test_exact_hour(self):
        self.assertEqual(
            format_duration(3600, style="descriptive"), "1h 0m 0s"
        )


class TestFormatFileSize(unittest.TestCase):
    """Tests for format_file_size."""

    def test_zero(self):
        self.assertEqual(format_file_size(0), "0 B")

    def test_negative(self):
        self.assertEqual(format_file_size(-10), "0 B")

    def test_none(self):
        self.assertEqual(format_file_size(None), "0 B")

    def test_bytes(self):
        self.assertEqual(format_file_size(512), "512.0 B")

    def test_kilobytes(self):
        self.assertEqual(format_file_size(2048), "2.0 KB")

    def test_megabytes(self):
        self.assertEqual(format_file_size(5 * 1024 * 1024), "5.0 MB")

    def test_gigabytes(self):
        self.assertEqual(format_file_size(3 * 1024**3), "3.0 GB")

    def test_terabytes(self):
        self.assertEqual(format_file_size(2 * 1024**4), "2.0 TB")

    def test_fractional(self):
        self.assertEqual(format_file_size(1536), "1.5 KB")


class TestParseDatetime(unittest.TestCase):
    """Tests for parse_datetime."""

    def test_none_returns_none(self):
        self.assertIsNone(parse_datetime(None))

    def test_empty_string(self):
        self.assertIsNone(parse_datetime(""))

    def test_iso_string(self):
        result = parse_datetime("2026-01-15T09:30:00")
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.hour, 9)

    def test_iso_string_with_z(self):
        result = parse_datetime("2026-01-15T09:30:00Z")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.tzinfo, timezone.utc)

    def test_datetime_passthrough(self):
        dt = datetime(2026, 2, 14, 12, 0)
        self.assertIs(parse_datetime(dt), dt)

    def test_invalid_string_returns_none(self):
        self.assertIsNone(parse_datetime("not-a-date"))

    def test_invalid_type_returns_none(self):
        self.assertIsNone(parse_datetime(12345))


class TestOpenWithSystemApp(unittest.TestCase):
    """Tests for open_with_system_app."""

    @patch("utils.formatting.platform.system", return_value="Linux")
    @patch("utils.formatting.subprocess.run")
    def test_linux_uses_xdg_open(self, mock_run, mock_system):
        open_with_system_app("/tmp/test.txt")
        mock_run.assert_called_once_with(
            ["xdg-open", "/tmp/test.txt"], check=True
        )

    @patch("utils.formatting.platform.system", return_value="Darwin")
    @patch("utils.formatting.subprocess.run")
    def test_macos_uses_open(self, mock_run, mock_system):
        open_with_system_app("/tmp/test.txt")
        mock_run.assert_called_once_with(
            ["open", "/tmp/test.txt"], check=True
        )

    @patch("utils.formatting.platform.system", return_value="Windows")
    @patch("utils.formatting.os.startfile", create=True)
    def test_windows_uses_startfile(self, mock_startfile, mock_system):
        open_with_system_app("C:\\test.txt")
        mock_startfile.assert_called_once_with("C:\\test.txt")


if __name__ == '__main__':
    unittest.main()
