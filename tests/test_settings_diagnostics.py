"""
Unit tests for settings diagnostics (BEAN-024).
"""

import os
import sys
import stat
import tempfile
import shutil
import types
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Ensure openai module exists (mock if not installed)
try:
    import openai as _real_openai  # noqa: F401
except ImportError:
    _openai_mock = types.ModuleType("openai")
    _openai_mock.OpenAI = MagicMock()

    class _AuthErr(Exception):
        def __init__(self, message="", response=None, body=None):
            super().__init__(message)
            self.response = response
            self.body = body

    class _ConnErr(Exception):
        def __init__(self, request=None):
            super().__init__("Connection error")
            self.request = request

    _openai_mock.AuthenticationError = _AuthErr
    _openai_mock.PermissionDeniedError = type("PermErr", (Exception,), {})
    _openai_mock.RateLimitError = type("RateErr", (Exception,), {})
    _openai_mock.APIConnectionError = _ConnErr
    sys.modules["openai"] = _openai_mock

from gui.settings_diagnostics import (  # noqa: E402
    check_directory,
    check_openai_api_key,
    run_all_checks,
    DiagnosticResult,
)
from config.settings import SettingsManager  # noqa: E402


class TestCheckDirectory(unittest.TestCase):
    """Tests for check_directory."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_existing_writable_dir_passes(self):
        result = check_directory(self.temp_dir, "Test dir")
        self.assertEqual(result.status, "pass")
        self.assertTrue(result.passed)

    def test_missing_dir_fails(self):
        result = check_directory("/nonexistent/path/xyz", "Missing dir")
        self.assertEqual(result.status, "fail")
        self.assertIn("does not exist", result.message)

    def test_file_instead_of_dir_fails(self):
        tmp_file = os.path.join(self.temp_dir, "afile.txt")
        with open(tmp_file, "w") as f:
            f.write("x")
        result = check_directory(tmp_file, "File path")
        self.assertEqual(result.status, "fail")
        self.assertIn("not a directory", result.message)

    def test_non_writable_dir_fails(self):
        ro_dir = os.path.join(self.temp_dir, "readonly")
        os.makedirs(ro_dir)
        os.chmod(ro_dir, stat.S_IRUSR | stat.S_IXUSR)
        try:
            result = check_directory(ro_dir, "Read-only dir")
            self.assertEqual(result.status, "fail")
            self.assertIn("not writable", result.message)
        finally:
            # Restore permissions so tearDown can clean up
            os.chmod(ro_dir, stat.S_IRWXU)

    def test_label_appears_in_name(self):
        result = check_directory(self.temp_dir, "Recordings directory")
        self.assertEqual(result.name, "Recordings directory")


class TestCheckOpenAIAPIKey(unittest.TestCase):
    """Tests for check_openai_api_key."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_file = self.temp_dir / "settings.json"
        self.manager = SettingsManager(config_file=str(self.config_file))

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_skip_when_not_needed(self):
        result = check_openai_api_key(self.manager, needs_api_key=False)
        self.assertEqual(result.status, "skip")
        self.assertIn("Not required", result.message)

    def test_fail_when_no_key_configured(self):
        with patch.object(self.manager, 'get_openai_api_key',
                          return_value=None):
            result = check_openai_api_key(self.manager, needs_api_key=True)
            self.assertEqual(result.status, "fail")
            self.assertIn("No API key", result.message)

    def test_pass_with_valid_key(self):
        key = "sk-" + "a" * 45
        with patch.object(self.manager, 'get_openai_api_key',
                          return_value=key), \
             patch.object(self.manager, 'validate_openai_api_key_live',
                          return_value=(True, "API key is valid and active.")):
            result = check_openai_api_key(self.manager, needs_api_key=True)
            self.assertEqual(result.status, "pass")

    def test_fail_with_invalid_key(self):
        key = "sk-" + "a" * 45
        with patch.object(self.manager, 'get_openai_api_key',
                          return_value=key), \
             patch.object(self.manager, 'validate_openai_api_key_live',
                          return_value=(False, "Invalid or revoked.")):
            result = check_openai_api_key(self.manager, needs_api_key=True)
            self.assertEqual(result.status, "fail")
            self.assertIn("Invalid", result.message)

    def test_timeout_returns_fail(self):
        key = "sk-" + "a" * 45

        def slow_validate(k):
            import time
            time.sleep(5)
            return (True, "ok")

        with patch.object(self.manager, 'get_openai_api_key',
                          return_value=key), \
             patch.object(self.manager, 'validate_openai_api_key_live',
                          side_effect=slow_validate):
            result = check_openai_api_key(
                self.manager, needs_api_key=True, timeout=0.1
            )
            self.assertEqual(result.status, "fail")
            self.assertIn("timed out", result.message)


class TestCheckMicrophone(unittest.TestCase):
    """Tests for check_microphone."""

    def test_success_with_mock_pyaudio(self):
        mock_pa_instance = MagicMock()
        mock_stream = MagicMock()
        mock_pa_instance.open.return_value = mock_stream

        mock_pyaudio = MagicMock()
        mock_pyaudio.PyAudio.return_value = mock_pa_instance
        mock_pyaudio.paInt16 = 8

        with patch.dict('sys.modules', {'pyaudio': mock_pyaudio}):
            # Re-import to pick up the mock
            from gui import settings_diagnostics as mod
            import importlib
            importlib.reload(mod)
            result = mod.check_microphone(device_index=None)

        self.assertEqual(result.status, "pass")
        self.assertIn("accessible", result.message)

    def test_failure_when_pyaudio_raises(self):
        mock_pa_instance = MagicMock()
        mock_pa_instance.open.side_effect = OSError("No device")

        mock_pyaudio = MagicMock()
        mock_pyaudio.PyAudio.return_value = mock_pa_instance
        mock_pyaudio.paInt16 = 8

        with patch.dict('sys.modules', {'pyaudio': mock_pyaudio}):
            from gui import settings_diagnostics as mod
            import importlib
            importlib.reload(mod)
            result = mod.check_microphone(device_index=0)

        self.assertEqual(result.status, "fail")
        self.assertIn("Could not open", result.message)

    def test_failure_when_pyaudio_not_installed(self):
        with patch.dict('sys.modules', {'pyaudio': None}):
            from gui import settings_diagnostics as mod
            import importlib
            importlib.reload(mod)
            result = mod.check_microphone()

        self.assertEqual(result.status, "fail")
        self.assertIn("not installed", result.message)


class TestRunAllChecks(unittest.TestCase):
    """Integration test for run_all_checks."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.rec_dir = os.path.join(self.temp_dir, "recordings")
        self.vault_dir = os.path.join(self.temp_dir, "vault")
        os.makedirs(self.rec_dir)
        os.makedirs(self.vault_dir)

        config_file = os.path.join(self.temp_dir, "settings.json")
        self.manager = SettingsManager(config_file=config_file)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_returns_four_results(self):
        with patch(
            'gui.settings_diagnostics.check_microphone',
            return_value=DiagnosticResult(
                "Microphone Access", "pass", "OK"
            ),
        ):
            results = run_all_checks(
                self.manager, self.rec_dir, self.vault_dir,
                device_index=None, needs_api_key=False,
            )
        self.assertEqual(len(results), 4)
        names = [r.name for r in results]
        self.assertIn("Recordings directory", names)
        self.assertIn("Vault directory", names)
        self.assertIn("OpenAI API Key", names)
        self.assertIn("Microphone Access", names)

    def test_all_pass_when_configured(self):
        with patch(
            'gui.settings_diagnostics.check_microphone',
            return_value=DiagnosticResult(
                "Microphone Access", "pass", "OK"
            ),
        ):
            results = run_all_checks(
                self.manager, self.rec_dir, self.vault_dir,
                device_index=None, needs_api_key=False,
            )
        for r in results:
            self.assertIn(r.status, ("pass", "skip"), f"{r.name}: {r.message}")


class TestDiagnosticResult(unittest.TestCase):
    """Test DiagnosticResult dataclass."""

    def test_passed_property_true(self):
        r = DiagnosticResult("Test", "pass", "OK")
        self.assertTrue(r.passed)

    def test_passed_property_false_for_fail(self):
        r = DiagnosticResult("Test", "fail", "Bad")
        self.assertFalse(r.passed)

    def test_passed_property_false_for_skip(self):
        r = DiagnosticResult("Test", "skip", "Skipped")
        self.assertFalse(r.passed)


if __name__ == '__main__':
    unittest.main()
