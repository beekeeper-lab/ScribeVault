"""
Unit tests for API key validation and secure storage (BEAN-004).
"""

import json
import os
import sys
import tempfile
import shutil
import types
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Create mock openai module if not installed
_openai_mock = None
try:
    import openai as _real_openai  # noqa: F401
except ImportError:
    _openai_mock = types.ModuleType("openai")
    _openai_mock.OpenAI = MagicMock()

    class _MockAuthenticationError(Exception):
        def __init__(self, message="", response=None, body=None):
            super().__init__(message)
            self.response = response
            self.body = body

    class _MockPermissionDeniedError(Exception):
        pass

    class _MockRateLimitError(Exception):
        pass

    class _MockAPIConnectionError(Exception):
        def __init__(self, request=None):
            super().__init__("Connection error")
            self.request = request

    _openai_mock.AuthenticationError = _MockAuthenticationError
    _openai_mock.PermissionDeniedError = _MockPermissionDeniedError
    _openai_mock.RateLimitError = _MockRateLimitError
    _openai_mock.APIConnectionError = _MockAPIConnectionError
    sys.modules["openai"] = _openai_mock

from config.settings import SettingsManager  # noqa: E402


class TestAPIKeyFormatValidation(unittest.TestCase):
    """Test API key format validation logic."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_file = self.temp_dir / "settings.json"
        self.manager = SettingsManager(config_file=str(self.config_file))

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_valid_key_format(self):
        """Valid sk- prefixed key of sufficient length should pass."""
        self.assertTrue(self.manager.validate_openai_api_key("sk-abc123def456ghi789jkl"))

    def test_valid_key_with_project_prefix(self):
        """Keys with sk-proj- prefix should also be valid."""
        key = "sk-proj-" + "a" * 40
        self.assertTrue(self.manager.validate_openai_api_key(key))

    def test_invalid_key_no_prefix(self):
        """Key without sk- prefix should fail."""
        self.assertFalse(self.manager.validate_openai_api_key("abc123def456ghi789jkl"))

    def test_invalid_key_too_short(self):
        """Key shorter than 20 characters should fail."""
        self.assertFalse(self.manager.validate_openai_api_key("sk-short"))

    def test_invalid_key_empty(self):
        """Empty string should fail."""
        self.assertFalse(self.manager.validate_openai_api_key(""))

    def test_invalid_key_none(self):
        """None should fail."""
        self.assertFalse(self.manager.validate_openai_api_key(None))

    def test_invalid_key_placeholder(self):
        """Placeholder values should fail."""
        self.assertFalse(self.manager.validate_openai_api_key("sk-your-api-key-here"))

    def test_key_with_whitespace_trimmed(self):
        """Whitespace around key should be trimmed and still validate."""
        key = "  sk-abc123def456ghi789jkl  "
        self.assertTrue(self.manager.validate_openai_api_key(key))

    def test_non_string_input(self):
        """Non-string inputs should fail."""
        self.assertFalse(self.manager.validate_openai_api_key(12345))
        self.assertFalse(self.manager.validate_openai_api_key(["sk-key"]))


class TestAPIKeyLiveValidation(unittest.TestCase):
    """Test live API key validation with mocked OpenAI client."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_file = self.temp_dir / "settings.json"
        self.manager = SettingsManager(config_file=str(self.config_file))

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_format_failure_returns_early(self):
        """Invalid format should fail without making API call."""
        is_valid, message = self.manager.validate_openai_api_key_live("bad-key")
        self.assertFalse(is_valid)
        self.assertIn("format", message.lower())

    def test_valid_key_passes_live_check(self):
        """Valid key that passes API call should return success."""
        import openai
        mock_client = MagicMock()
        mock_client.models.list.return_value = MagicMock()
        with patch.object(openai, "OpenAI", return_value=mock_client):
            key = "sk-" + "a" * 45
            is_valid, message = self.manager.validate_openai_api_key_live(key)
            self.assertTrue(is_valid)
            self.assertIn("valid", message.lower())

    def test_auth_error_returns_invalid(self):
        """AuthenticationError should report invalid key."""
        import openai
        mock_client = MagicMock()
        mock_client.models.list.side_effect = openai.AuthenticationError(
            message="Invalid API key",
            response=MagicMock(status_code=401),
            body=None,
        )
        with patch.object(openai, "OpenAI", return_value=mock_client):
            key = "sk-" + "a" * 45
            is_valid, message = self.manager.validate_openai_api_key_live(key)
            self.assertFalse(is_valid)
            self.assertIn("invalid", message.lower())

    def test_connection_error_reports_network(self):
        """APIConnectionError should suggest network issue."""
        import openai
        mock_client = MagicMock()
        mock_client.models.list.side_effect = openai.APIConnectionError(
            request=MagicMock()
        )
        with patch.object(openai, "OpenAI", return_value=mock_client):
            key = "sk-" + "a" * 45
            is_valid, message = self.manager.validate_openai_api_key_live(key)
            self.assertFalse(is_valid)
            self.assertIn("connect", message.lower())


class TestEncryptedConfigStorage(unittest.TestCase):
    """Test encrypted config file storage (keyring unavailable scenario)."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_file = self.temp_dir / "settings.json"
        self.manager = SettingsManager(config_file=str(self.config_file))

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_write_and_read_encrypted_key(self):
        """Write key to encrypted config and read it back."""
        test_key = "sk-test-secret-key-for-testing-12345"
        self.manager._write_encrypted_key(test_key)

        enc_path = self.manager._get_encrypted_config_path()
        self.assertTrue(enc_path.exists())

        # Read it back
        result = self.manager._read_encrypted_key()
        self.assertEqual(result, test_key)

    def test_encrypted_file_not_plaintext(self):
        """Encrypted file should not contain the raw key."""
        test_key = "sk-test-secret-key-for-testing-12345"
        self.manager._write_encrypted_key(test_key)

        enc_path = self.manager._get_encrypted_config_path()
        content = enc_path.read_text()
        self.assertNotIn(test_key, content)

    def test_encrypted_file_has_restricted_permissions(self):
        """Encrypted config should have 600 permissions."""
        test_key = "sk-test-secret-key-for-testing-12345"
        self.manager._write_encrypted_key(test_key)

        enc_path = self.manager._get_encrypted_config_path()
        mode = oct(enc_path.stat().st_mode)[-3:]
        self.assertEqual(mode, "600")

    def test_delete_encrypted_key(self):
        """Deleting encrypted key should remove the file."""
        test_key = "sk-test-secret-key-for-testing-12345"
        self.manager._write_encrypted_key(test_key)

        enc_path = self.manager._get_encrypted_config_path()
        self.assertTrue(enc_path.exists())

        self.manager._delete_encrypted_key()
        self.assertFalse(enc_path.exists())

    def test_read_nonexistent_returns_none(self):
        """Reading when no encrypted config exists returns None."""
        result = self.manager._read_encrypted_key()
        self.assertIsNone(result)

    def test_encrypted_file_version(self):
        """Encrypted file should have version 3 format with salt."""
        test_key = "sk-test-secret-key-for-testing-12345"
        self.manager._write_encrypted_key(test_key)

        enc_path = self.manager._get_encrypted_config_path()
        with open(enc_path) as f:
            data = json.load(f)

        self.assertEqual(data["version"], 3)
        self.assertEqual(data["method"], "fernet")
        self.assertIn("salt", data)

    def test_salt_is_unique_per_write(self):
        """Each write should produce a different salt."""
        test_key = "sk-test-secret-key-for-testing-12345"
        self.manager._write_encrypted_key(test_key)
        enc_path = self.manager._get_encrypted_config_path()
        with open(enc_path) as f:
            salt1 = json.load(f)["salt"]

        self.manager._write_encrypted_key(test_key)
        with open(enc_path) as f:
            salt2 = json.load(f)["salt"]

        self.assertNotEqual(salt1, salt2)


class TestLegacyEncryptionMigration(unittest.TestCase):
    """Test migration from legacy version 2 encryption formats."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_file = self.temp_dir / "settings.json"
        self.manager = SettingsManager(config_file=str(self.config_file))

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_migrate_legacy_fernet(self):
        """Legacy version 2 Fernet data should be readable and migrated."""
        import base64
        import hashlib
        from cryptography.fernet import Fernet

        test_key = "sk-legacy-fernet-key-for-testing-12345"
        # Write legacy version 2 fernet format (no salt)
        import getpass
        import platform
        machine_id = (
            f"ScribeVault-{getpass.getuser()}-{platform.node()}"
        )
        legacy_key = hashlib.sha256(machine_id.encode()).digest()
        fernet = Fernet(base64.urlsafe_b64encode(legacy_key))
        encrypted = fernet.encrypt(test_key.encode())

        enc_path = self.manager._get_encrypted_config_path()
        enc_path.parent.mkdir(exist_ok=True)
        with open(enc_path, "w") as f:
            json.dump({
                "version": 2,
                "data": encrypted.decode(),
                "method": "fernet",
            }, f)

        # Read should succeed and auto-migrate
        result = self.manager._read_encrypted_key()
        self.assertEqual(result, test_key)

        # File should now be version 3 with salt
        with open(enc_path) as f:
            data = json.load(f)
        self.assertEqual(data["version"], 3)
        self.assertIn("salt", data)

    def test_migrate_legacy_xor(self):
        """Legacy version 2 XOR data should be readable and migrated."""
        import base64
        import hashlib

        test_key = "sk-legacy-xor-key-for-testing-12345"
        # Write legacy version 2 XOR format
        import getpass
        import platform
        machine_id = (
            f"ScribeVault-{getpass.getuser()}-{platform.node()}"
        )
        legacy_key = hashlib.sha256(machine_id.encode()).digest()
        xor_bytes = bytes(
            b ^ legacy_key[i % len(legacy_key)]
            for i, b in enumerate(test_key.encode())
        )

        enc_path = self.manager._get_encrypted_config_path()
        enc_path.parent.mkdir(exist_ok=True)
        with open(enc_path, "w") as f:
            json.dump({
                "version": 2,
                "data": base64.urlsafe_b64encode(xor_bytes).decode(),
                "method": "xor",
            }, f)

        # Read should succeed and auto-migrate
        result = self.manager._read_encrypted_key()
        self.assertEqual(result, test_key)

        # File should now be version 3 with salt
        with open(enc_path) as f:
            data = json.load(f)
        self.assertEqual(data["version"], 3)
        self.assertIn("salt", data)

    def test_unsupported_version_returns_none(self):
        """Unsupported version should return None."""
        enc_path = self.manager._get_encrypted_config_path()
        enc_path.parent.mkdir(exist_ok=True)
        with open(enc_path, "w") as f:
            json.dump({"version": 99, "data": "x", "method": "y"}, f)

        result = self.manager._read_encrypted_key()
        self.assertIsNone(result)


class TestAPIKeyPriorityChain(unittest.TestCase):
    """Test get_openai_api_key priority: keyring -> encrypted -> env."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_file = self.temp_dir / "settings.json"
        self.manager = SettingsManager(config_file=str(self.config_file))

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @patch("config.settings.KEYRING_AVAILABLE", False)
    @patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False)
    def test_no_key_returns_none(self):
        """With no keyring, no encrypted config, and no env var, returns None."""
        manager = SettingsManager(config_file=str(self.config_file))
        result = manager.get_openai_api_key()
        self.assertIsNone(result)

    @patch("config.settings.KEYRING_AVAILABLE", False)
    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-env-var-key-for-test-12345"}, clear=False)
    def test_env_var_fallback(self):
        """With no keyring or encrypted config, env var should be used."""
        manager = SettingsManager(config_file=str(self.config_file))
        result = manager.get_openai_api_key()
        self.assertEqual(result, "sk-env-var-key-for-test-12345")

    @patch("config.settings.KEYRING_AVAILABLE", False)
    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-env-var-key-for-test-12345"}, clear=False)
    def test_encrypted_config_over_env(self):
        """Encrypted config should take priority over env var."""
        manager = SettingsManager(config_file=str(self.config_file))
        encrypted_key = "sk-encrypted-config-key-for-test-12345"
        manager._write_encrypted_key(encrypted_key)

        result = manager.get_openai_api_key()
        self.assertEqual(result, encrypted_key)

    def test_has_openai_api_key_false_when_empty(self):
        """has_openai_api_key should return False when no key is set."""
        with patch.object(self.manager, 'get_openai_api_key', return_value=None):
            self.assertFalse(self.manager.has_openai_api_key())

    def test_has_openai_api_key_false_for_placeholder(self):
        """has_openai_api_key should return False for placeholder values."""
        with patch.object(self.manager, 'get_openai_api_key', return_value="your-openai-api-key-here"):
            self.assertFalse(self.manager.has_openai_api_key())

    def test_has_openai_api_key_true_for_valid(self):
        """has_openai_api_key should return True for a real key."""
        with patch.object(self.manager, 'get_openai_api_key', return_value="sk-real-key-12345-abcde"):
            self.assertTrue(self.manager.has_openai_api_key())


class TestSaveOpenAIAPIKey(unittest.TestCase):
    """Test save_openai_api_key with different storage backends."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_file = self.temp_dir / "settings.json"
        self.manager = SettingsManager(config_file=str(self.config_file))

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @patch("config.settings.KEYRING_AVAILABLE", False)
    def test_save_to_encrypted_when_no_keyring(self):
        """When keyring unavailable, key should be saved to encrypted config."""
        manager = SettingsManager(config_file=str(self.config_file))
        test_key = "sk-test-save-key-encrypted-12345"
        manager.save_openai_api_key(test_key)

        enc_path = manager._get_encrypted_config_path()
        self.assertTrue(enc_path.exists())

        result = manager._read_encrypted_key()
        self.assertEqual(result, test_key)

    @patch("config.settings.KEYRING_AVAILABLE", False)
    def test_save_empty_deletes_encrypted(self):
        """Saving empty key should delete encrypted config."""
        manager = SettingsManager(config_file=str(self.config_file))
        test_key = "sk-test-save-key-encrypted-12345"
        manager.save_openai_api_key(test_key)

        enc_path = manager._get_encrypted_config_path()
        self.assertTrue(enc_path.exists())

        manager.save_openai_api_key("")
        self.assertFalse(enc_path.exists())

    @patch("config.settings.KEYRING_AVAILABLE", False)
    def test_save_does_not_create_env_file(self):
        """Saving a key should never create a .env file."""
        original_dir = os.getcwd()
        try:
            os.chdir(self.temp_dir)
            manager = SettingsManager(config_file=str(self.config_file))
            manager.save_openai_api_key("sk-test-no-env-file-created-12345")

            env_file = self.temp_dir / ".env"
            self.assertFalse(env_file.exists())
        finally:
            os.chdir(original_dir)


class TestStorageMethodDetection(unittest.TestCase):
    """Test get_api_key_storage_method."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_file = self.temp_dir / "settings.json"
        self.manager = SettingsManager(config_file=str(self.config_file))

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @patch("config.settings.KEYRING_AVAILABLE", False)
    @patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False)
    def test_no_key_returns_none_method(self):
        manager = SettingsManager(config_file=str(self.config_file))
        self.assertEqual(manager.get_api_key_storage_method(), "none")

    @patch("config.settings.KEYRING_AVAILABLE", False)
    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-env-key-for-method-test-12345"}, clear=False)
    def test_env_method_detected(self):
        manager = SettingsManager(config_file=str(self.config_file))
        self.assertEqual(manager.get_api_key_storage_method(), "environment")

    @patch("config.settings.KEYRING_AVAILABLE", False)
    def test_encrypted_method_detected(self):
        manager = SettingsManager(config_file=str(self.config_file))
        manager._write_encrypted_key("sk-test-method-detection-12345-abc")
        self.assertEqual(manager.get_api_key_storage_method(), "encrypted_config")


class TestSummarizerServiceInit(unittest.TestCase):
    """Test SummarizerService initialization with settings_manager."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_file = self.temp_dir / "settings.json"
        self.manager = SettingsManager(config_file=str(self.config_file))

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False)
    @patch("config.settings.KEYRING_AVAILABLE", False)
    def test_raises_without_api_key(self):
        """SummarizerService should raise ValueError with no API key."""
        from ai.summarizer import SummarizerService
        manager = SettingsManager(config_file=str(self.config_file))
        with self.assertRaises(ValueError) as ctx:
            SummarizerService(settings_manager=manager)
        self.assertIn("not configured", str(ctx.exception).lower())

    def test_initializes_with_settings_manager(self):
        """SummarizerService should use key from settings_manager."""
        import openai
        test_key = "sk-test-summarizer-init-key-12345"
        mock_openai_cls = MagicMock()
        with patch.object(self.manager, 'get_openai_api_key', return_value=test_key), \
             patch.object(openai, "OpenAI", mock_openai_cls):
            from ai.summarizer import SummarizerService
            SummarizerService(settings_manager=self.manager)
            mock_openai_cls.assert_called_with(api_key=test_key)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-env-fallback-key-test-12345"}, clear=False)
    def test_falls_back_to_env_without_manager(self):
        """SummarizerService should fall back to env var without manager."""
        import openai
        mock_openai_cls = MagicMock()
        with patch.object(openai, "OpenAI", mock_openai_cls):
            from ai.summarizer import SummarizerService
            SummarizerService()
            mock_openai_cls.assert_called_with(api_key="sk-env-fallback-key-test-12345")


if __name__ == '__main__':
    unittest.main()
