"""
Integration tests for ScribeVault application.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import threading
import time

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Note: These imports may show linter errors in the editor but will work when run


class TestScribeVaultIntegration(unittest.TestCase):
    """Integration tests for the complete ScribeVault workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create test audio file (fake WAV file)
        self.test_audio = self.temp_dir / "test_recording.wav"
        # Create a minimal WAV file header
        wav_header = (
            b'RIFF' +
            (44 + 1000).to_bytes(4, 'little') +  # File size - 8
            b'WAVE' +
            b'fmt ' +
            (16).to_bytes(4, 'little') +  # Subchunk1Size
            (1).to_bytes(2, 'little') +   # AudioFormat (PCM)
            (1).to_bytes(2, 'little') +   # NumChannels
            (44100).to_bytes(4, 'little') +  # SampleRate
            (88200).to_bytes(4, 'little') +  # ByteRate
            (2).to_bytes(2, 'little') +   # BlockAlign
            (16).to_bytes(2, 'little') +  # BitsPerSample
            b'data' +
            (1000).to_bytes(4, 'little') +  # Subchunk2Size
            b'\x00' * 1000  # Audio data
        )
        self.test_audio.write_bytes(wav_header)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_complete_recording_workflow(self):
        """Test the complete recording, transcription, and storage workflow."""
        try:
            from vault.manager import VaultManager
            from config.settings import SettingsManager
            
            # Initialize components
            settings_manager = SettingsManager()
            vault_manager = VaultManager(vault_dir=self.temp_dir)
            
            # Simulate adding a recording to the vault
            recording_id = vault_manager.add_recording(
                filename="test_recording.wav",
                title="Integration Test Recording",
                description="Test recording for integration test",
                category="meeting",
                duration=10.5,
                file_size=self.test_audio.stat().st_size,
                transcription="This is a test transcription for integration testing.",
                summary="Test summary of the recording content."
            )
            
            # Verify recording was added
            self.assertIsInstance(recording_id, int)
            self.assertGreater(recording_id, 0)
            
            # Retrieve and verify recording
            recordings = vault_manager.get_recordings()
            self.assertEqual(len(recordings), 1)
            
            recording = recordings[0]
            self.assertEqual(recording['id'], recording_id)
            self.assertEqual(recording['title'], "Integration Test Recording")
            self.assertEqual(recording['category'], "meeting")
            self.assertEqual(recording['transcription'], "This is a test transcription for integration testing.")
            
        except ImportError as e:
            self.skipTest(f"Cannot import required modules: {e}")
    
    def test_settings_and_vault_integration(self):
        """Test integration between settings and vault components."""
        try:
            from config.settings import SettingsManager
            from vault.manager import VaultManager
            
            # Initialize settings
            settings = SettingsManager()
            
            # Test that vault can be initialized with settings
            vault = VaultManager(vault_dir=self.temp_dir)
            
            # Add a recording with various settings-dependent features
            recording_id = vault.add_recording(
                filename="settings_test.wav",
                title="Settings Integration Test",
                category="uncategorized"  # Default category
            )

            self.assertGreater(recording_id, 0)

            # Test retrieval with filtering
            recordings = vault.get_recordings(category="uncategorized")
            self.assertEqual(len(recordings), 1)
            self.assertEqual(recordings[0]['category'], "uncategorized")
            
        except ImportError as e:
            self.skipTest(f"Cannot import required modules: {e}")
    
    def test_error_handling_integration(self):
        """Test error handling across different components."""
        try:
            from vault.manager import VaultManager, VaultException
            
            vault = VaultManager(vault_dir=self.temp_dir)
            
            # Test that errors are properly propagated
            with self.assertRaises(VaultException):
                vault.add_recording(filename="")  # Empty filename
            
            # Invalid category should be auto-corrected to 'uncategorized'
            corrected_id = vault.add_recording(
                filename="test.wav",
                category="invalid_category"
            )
            self.assertGreater(corrected_id, 0)
            corrected = vault.get_recordings()
            self.assertEqual(corrected[0]['category'], "uncategorized")

            # Test that valid operations still work after errors
            recording_id = vault.add_recording(filename="valid.wav")
            self.assertGreater(recording_id, 0)
            
        except ImportError as e:
            self.skipTest(f"Cannot import required modules: {e}")
    
    def test_concurrent_vault_operations(self):
        """Test vault operations under concurrent access."""
        try:
            from vault.manager import VaultManager
            
            vault = VaultManager(vault_dir=self.temp_dir)
            results = []
            errors = []
            
            def add_recording(index):
                try:
                    recording_id = vault.add_recording(
                        filename=f"concurrent_{index}.wav",
                        title=f"Concurrent Recording {index}"
                    )
                    results.append(recording_id)
                except Exception as e:
                    errors.append(e)
            
            # Create multiple threads to add recordings concurrently
            threads = []
            for i in range(5):
                thread = threading.Thread(target=add_recording, args=(i,))
                threads.append(thread)
            
            # Start all threads
            for thread in threads:
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Check results
            self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
            self.assertEqual(len(results), 5)
            self.assertEqual(len(set(results)), 5)  # All IDs should be unique
            
            # Verify all recordings were added
            recordings = vault.get_recordings()
            self.assertEqual(len(recordings), 5)
            
        except ImportError as e:
            self.skipTest(f"Cannot import required modules: {e}")
    
    def test_database_integrity(self):
        """Test database integrity under various operations."""
        try:
            from vault.manager import VaultManager
            import sqlite3
            
            vault = VaultManager(vault_dir=self.temp_dir)
            
            # Add some test data
            ids = []
            for i in range(3):
                recording_id = vault.add_recording(
                    filename=f"integrity_test_{i}.wav",
                    title=f"Integrity Test {i}",
                    key_points=[f"Point {i}.1", f"Point {i}.2"],
                    tags=[f"tag{i}", "common"]
                )
                ids.append(recording_id)
            
            # Test database constraints are working
            with sqlite3.connect(vault.db_path) as conn:
                # Enable foreign keys (per-connection setting in SQLite)
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.execute("PRAGMA foreign_keys")
                foreign_keys_enabled = cursor.fetchone()[0]
                self.assertEqual(foreign_keys_enabled, 1)

                # Test unique constraint on filename
                with self.assertRaises(sqlite3.IntegrityError):
                    conn.execute(
                        "INSERT INTO recordings (filename) VALUES (?)",
                        ("integrity_test_0.wav",)
                    )
            
            # Test data consistency after operations
            recordings = vault.get_recordings()
            self.assertEqual(len(recordings), 3)
            
            # Verify JSON fields are properly handled
            for recording in recordings:
                self.assertIsInstance(recording['key_points'], list)
                self.assertIsInstance(recording['tags'], list)
                self.assertEqual(len(recording['key_points']), 2)
                self.assertIn("common", recording['tags'])
                
        except ImportError as e:
            self.skipTest(f"Cannot import required modules: {e}")


class TestComponentInteractions(unittest.TestCase):
    """Test interactions between different components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_settings_validation_with_vault(self):
        """Test that settings validation works with vault operations."""
        try:
            from config.settings import SettingsManager
            from vault.manager import VaultManager
            
            settings = SettingsManager()
            vault = VaultManager(vault_dir=self.temp_dir)
            
            # Test that valid categories from settings work with vault
            valid_categories = ["meeting", "interview", "lecture", "note", "uncategorized"]
            
            for category in valid_categories:
                recording_id = vault.add_recording(
                    filename=f"{category}_test.wav",
                    category=category
                )
                self.assertGreater(recording_id, 0)
            
            # Verify all recordings were added with correct categories
            recordings = vault.get_recordings()
            categories_found = {r['category'] for r in recordings}
            self.assertEqual(categories_found, set(valid_categories))
            
        except ImportError as e:
            self.skipTest(f"Cannot import required modules: {e}")


if __name__ == '__main__':
    unittest.main()
