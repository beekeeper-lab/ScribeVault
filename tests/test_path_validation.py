"""
Unit tests for path traversal protection (BEAN-027).
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from export.utils import validate_path_within


class TestValidatePathWithin(unittest.TestCase):
    """Test the validate_path_within utility."""

    def setUp(self):
        self.base_dir = Path(tempfile.mkdtemp())
        (self.base_dir / "subdir").mkdir()
        (self.base_dir / "subdir" / "file.txt").touch()

    def tearDown(self):
        import shutil
        if self.base_dir.exists():
            shutil.rmtree(self.base_dir)

    def test_valid_path_passes(self):
        """A path within base_dir should pass validation."""
        result = validate_path_within(
            self.base_dir / "subdir" / "file.txt", self.base_dir
        )
        self.assertTrue(str(result).startswith(str(self.base_dir.resolve())))

    def test_valid_relative_path_passes(self):
        """A relative path that resolves within base_dir should pass."""
        result = validate_path_within(
            self.base_dir / "subdir" / "." / "file.txt", self.base_dir
        )
        self.assertTrue(str(result).startswith(str(self.base_dir.resolve())))

    def test_dotdot_traversal_blocked(self):
        """A path with .. that escapes base_dir should be blocked."""
        with self.assertRaises(ValueError) as ctx:
            validate_path_within(
                self.base_dir / "subdir" / ".." / ".." / "etc" / "passwd",
                self.base_dir,
            )
        self.assertIn("Path traversal blocked", str(ctx.exception))

    def test_absolute_path_outside_blocked(self):
        """An absolute path outside base_dir should be blocked."""
        with self.assertRaises(ValueError):
            validate_path_within(Path("/etc/passwd"), self.base_dir)

    def test_symlink_traversal_blocked(self):
        """A symlink pointing outside base_dir should be blocked."""
        link_path = self.base_dir / "evil_link"
        try:
            link_path.symlink_to("/etc")
        except OSError:
            self.skipTest("Cannot create symlinks on this platform")

        with self.assertRaises(ValueError):
            validate_path_within(link_path / "passwd", self.base_dir)

    def test_base_dir_itself_passes(self):
        """The base_dir path itself should pass validation."""
        result = validate_path_within(self.base_dir, self.base_dir)
        self.assertEqual(result, self.base_dir.resolve())

    def test_returns_resolved_path(self):
        """The returned path should be fully resolved."""
        result = validate_path_within(
            self.base_dir / "subdir" / "file.txt", self.base_dir
        )
        self.assertEqual(result, result.resolve())


if __name__ == '__main__':
    unittest.main()
