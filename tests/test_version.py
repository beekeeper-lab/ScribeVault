"""
Unit tests for the version constant.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from version import __version__  # noqa: E402


class TestVersion(unittest.TestCase):
    """Verify the single-source version string."""

    def test_version_is_string(self):
        self.assertIsInstance(__version__, str)

    def test_version_format(self):
        parts = __version__.split(".")
        self.assertEqual(len(parts), 3)
        for part in parts:
            self.assertTrue(part.isdigit())

    def test_current_version(self):
        self.assertEqual(__version__, "2.0.0")


if __name__ == '__main__':
    unittest.main()
