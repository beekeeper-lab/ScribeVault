"""
Unit tests for secure file and directory permissions (BEAN-030).

Verifies that secure_mkdir and secure_file_permissions apply
restrictive POSIX permissions on supported platforms.
"""

import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from export.utils import secure_mkdir, secure_file_permissions


@unittest.skipUnless(os.name == "posix", "POSIX permissions only")
class TestSecureMkdir(unittest.TestCase):
    """Test that secure_mkdir creates directories with 0o700."""

    def test_directory_created_with_0700(self):
        """New directory should have owner-only permissions."""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "secure_dir"
            secure_mkdir(target)
            self.assertTrue(target.is_dir())
            mode = stat.S_IMODE(target.stat().st_mode)
            self.assertEqual(mode, 0o700)

    def test_nested_directory_created(self):
        """Nested directories should be created."""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "a" / "b" / "c"
            secure_mkdir(target)
            self.assertTrue(target.is_dir())
            mode = stat.S_IMODE(target.stat().st_mode)
            self.assertEqual(mode, 0o700)

    def test_existing_directory_permissions_tightened(self):
        """An existing directory should have permissions set."""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "existing"
            target.mkdir(mode=0o755)
            secure_mkdir(target)
            mode = stat.S_IMODE(target.stat().st_mode)
            self.assertEqual(mode, 0o700)

    def test_returns_path(self):
        """secure_mkdir should return the directory path."""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "ret"
            result = secure_mkdir(target)
            self.assertEqual(result, target)


@unittest.skipUnless(os.name == "posix", "POSIX permissions only")
class TestSecureFilePermissions(unittest.TestCase):
    """Test that secure_file_permissions sets 0o600 on files."""

    def test_file_set_to_0600(self):
        """File should be set to owner read/write only."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            path = Path(f.name)
        try:
            path.chmod(0o644)
            secure_file_permissions(path)
            mode = stat.S_IMODE(path.stat().st_mode)
            self.assertEqual(mode, 0o600)
        finally:
            path.unlink()

    def test_nonexistent_file_is_noop(self):
        """Non-existent file should not raise."""
        path = Path("/tmp/does_not_exist_test_030")
        secure_file_permissions(path)  # should not raise

    def test_custom_mode(self):
        """Custom mode should be applied."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            path = Path(f.name)
        try:
            secure_file_permissions(path, mode=0o400)
            mode = stat.S_IMODE(path.stat().st_mode)
            self.assertEqual(mode, 0o400)
        finally:
            path.chmod(0o600)
            path.unlink()


if __name__ == '__main__':
    unittest.main()
