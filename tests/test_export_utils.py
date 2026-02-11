"""
Tests for export utility functions (BEAN-018).
"""

import shutil
import tempfile
import unittest
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from export.utils import sanitize_title, create_unique_subfolder


class TestSanitizeTitle(unittest.TestCase):
    """Tests for sanitize_title()."""

    def test_basic_title(self):
        self.assertEqual(sanitize_title("Sprint Planning"), "Sprint_Planning")

    def test_special_characters_stripped(self):
        self.assertEqual(
            sanitize_title("Meeting #1 @Office!"),
            "Meeting_1_Office",
        )

    def test_hyphens_and_underscores_kept(self):
        self.assertEqual(
            sanitize_title("team-standup_daily"),
            "team-standup_daily",
        )

    def test_truncation_to_max_length(self):
        long_title = "A" * 100
        result = sanitize_title(long_title)
        self.assertEqual(len(result), 50)

    def test_custom_max_length(self):
        result = sanitize_title("Hello World", max_length=5)
        self.assertEqual(result, "Hello")

    def test_empty_string_returns_untitled(self):
        self.assertEqual(sanitize_title(""), "Untitled")

    def test_only_special_chars_returns_untitled(self):
        self.assertEqual(sanitize_title("!@#$%^&*()"), "Untitled")

    def test_leading_trailing_spaces_stripped(self):
        self.assertEqual(sanitize_title("  Hello World  "), "Hello_World")

    def test_unicode_letters_kept(self):
        # Unicode alphanumeric chars should be kept via isalnum()
        result = sanitize_title("Reunion de equipo")
        self.assertEqual(result, "Reunion_de_equipo")

    def test_tabs_and_newlines_stripped(self):
        self.assertEqual(sanitize_title("Hello\tWorld\n"), "HelloWorld")


class TestCreateUniqueSubfolder(unittest.TestCase):
    """Tests for create_unique_subfolder()."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_creates_subfolder(self):
        result = create_unique_subfolder(self.temp_dir, "Sprint_Planning")
        self.assertTrue(result.exists())
        self.assertTrue(result.is_dir())
        self.assertEqual(result.name, "Sprint_Planning")

    def test_duplicate_gets_suffix(self):
        first = create_unique_subfolder(self.temp_dir, "Meeting")
        second = create_unique_subfolder(self.temp_dir, "Meeting")
        self.assertEqual(first.name, "Meeting")
        self.assertEqual(second.name, "Meeting_2")
        self.assertTrue(second.exists())

    def test_multiple_duplicates(self):
        create_unique_subfolder(self.temp_dir, "Notes")
        create_unique_subfolder(self.temp_dir, "Notes")
        third = create_unique_subfolder(self.temp_dir, "Notes")
        self.assertEqual(third.name, "Notes_3")

    def test_returns_path_object(self):
        result = create_unique_subfolder(self.temp_dir, "Test")
        self.assertIsInstance(result, Path)

    def test_subfolder_is_child_of_parent(self):
        result = create_unique_subfolder(self.temp_dir, "Child")
        self.assertEqual(result.parent, self.temp_dir)


if __name__ == '__main__':
    unittest.main()
