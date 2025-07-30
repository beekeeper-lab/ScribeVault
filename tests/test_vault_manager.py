"""
Unit tests for VaultManager class.
"""

import unittest
import tempfile
import shutil
import sqlite3
from pathlib import Path
import json

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from vault.manager import VaultManager, VaultException


class TestVaultManager(unittest.TestCase):
    """Test cases for VaultManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.vault_manager = VaultManager(vault_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test vault manager initialization."""
        self.assertTrue(self.temp_dir.exists())
        self.assertTrue((self.temp_dir / "scribevault.db").exists())
    
    def test_add_recording_success(self):
        """Test successful recording addition."""
        recording_id = self.vault_manager.add_recording(
            filename="test.wav",
            title="Test Recording",
            description="Test description",
            category="meeting",
            duration=120.5,
            file_size=1024
        )
        
        self.assertIsInstance(recording_id, int)
        self.assertGreater(recording_id, 0)
    
    def test_add_recording_validation(self):
        """Test recording addition with validation."""
        # Test empty filename - should raise exception
        with self.assertRaises(VaultException):
            self.vault_manager.add_recording(filename="")
        
        with self.assertRaises(VaultException):
            self.vault_manager.add_recording(filename="   ")  # Whitespace only
        
        # Test invalid category - should be corrected, not rejected
        recording_id = self.vault_manager.add_recording(
            filename="test.wav",
            category="invalid_category"
        )
        # Verify it was corrected to 'other'
        recordings = self.vault_manager.get_recordings()
        self.assertEqual(recordings[0]['category'], "other")
        
        # Test negative values - should be corrected, not rejected
        recording_id2 = self.vault_manager.add_recording(
            filename="test2.wav",
            duration=-1.0,
            file_size=-100
        )
        recordings = self.vault_manager.get_recordings()
        test2_recording = next(r for r in recordings if r['filename'] == 'test2.wav')
        self.assertEqual(test2_recording['duration'], 0.0)
        self.assertEqual(test2_recording['file_size'], 0)
    
    def test_add_recording_duplicate_filename(self):
        """Test adding recording with duplicate filename."""
        # Add first recording
        self.vault_manager.add_recording(filename="test.wav")
        
        # Try to add duplicate
        with self.assertRaises(VaultException):
            self.vault_manager.add_recording(filename="test.wav")
    
    def test_get_recordings_basic(self):
        """Test basic recording retrieval."""
        # Add test recordings
        id1 = self.vault_manager.add_recording(
            filename="test1.wav",
            title="Recording 1",
            category="meeting"
        )
        id2 = self.vault_manager.add_recording(
            filename="test2.wav",
            title="Recording 2",
            category="interview"
        )
        
        # Get all recordings
        recordings = self.vault_manager.get_recordings()
        self.assertEqual(len(recordings), 2)
        
        # Check data integrity
        recording_ids = [r['id'] for r in recordings]
        self.assertIn(id1, recording_ids)
        self.assertIn(id2, recording_ids)
    
    def test_get_recordings_filtering(self):
        """Test recording retrieval with filtering."""
        # Add test recordings
        self.vault_manager.add_recording(
            filename="meeting1.wav",
            title="Meeting Recording",
            category="meeting"
        )
        self.vault_manager.add_recording(
            filename="interview1.wav",
            title="Interview Recording",
            category="interview"
        )
        
        # Filter by category
        meetings = self.vault_manager.get_recordings(category="meeting")
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0]['category'], "meeting")
        
        # Filter by search query
        search_results = self.vault_manager.get_recordings(search_query="Meeting")
        self.assertEqual(len(search_results), 1)
        self.assertEqual(search_results[0]['title'], "Meeting Recording")
    
    def test_get_recordings_pagination(self):
        """Test recording retrieval with pagination."""
        # Add multiple recordings
        for i in range(5):
            self.vault_manager.add_recording(filename=f"test{i}.wav")
        
        # Test limit
        limited = self.vault_manager.get_recordings(limit=3)
        self.assertEqual(len(limited), 3)
        
        # Test offset
        offset_results = self.vault_manager.get_recordings(limit=2, offset=2)
        self.assertEqual(len(offset_results), 2)
        
        # Test invalid pagination
        with self.assertRaises(VaultException):
            self.vault_manager.get_recordings(limit=-1)
        
        with self.assertRaises(VaultException):
            self.vault_manager.get_recordings(offset=-1)
    
    def test_update_recording_success(self):
        """Test successful recording update."""
        # Add recording
        recording_id = self.vault_manager.add_recording(filename="test.wav")
        
        # Update recording
        success = self.vault_manager.update_recording(
            recording_id,
            title="Updated Title",
            description="Updated Description"
        )
        
        self.assertTrue(success)
        
        # Verify update
        recordings = self.vault_manager.get_recordings()
        updated = next(r for r in recordings if r['id'] == recording_id)
        self.assertEqual(updated['title'], "Updated Title")
        self.assertEqual(updated['description'], "Updated Description")
    
    def test_update_recording_validation(self):
        """Test recording update with validation."""
        recording_id = self.vault_manager.add_recording(filename="test.wav")
        
        # Test invalid recording ID
        with self.assertRaises(VaultException):
            self.vault_manager.update_recording(-1, title="Test")
        
        # Test non-existent recording
        with self.assertRaises(VaultException):
            self.vault_manager.update_recording(99999, title="Test")
        
        # Test invalid category - should be corrected, not rejected
        success = self.vault_manager.update_recording(
            recording_id, 
            category="invalid_category"
        )
        self.assertTrue(success)
        
        # Verify category was corrected
        recordings = self.vault_manager.get_recordings()
        updated = next(r for r in recordings if r['id'] == recording_id)
        self.assertEqual(updated['category'], "other")
    
    def test_delete_recording_success(self):
        """Test successful recording deletion."""
        # Add recording
        recording_id = self.vault_manager.add_recording(filename="test.wav")
        
        # Delete recording
        success = self.vault_manager.delete_recording(recording_id)
        self.assertTrue(success)
        
        # Verify deletion
        recordings = self.vault_manager.get_recordings()
        self.assertEqual(len(recordings), 0)
    
    def test_delete_recording_validation(self):
        """Test recording deletion with validation."""
        # Test invalid recording ID
        with self.assertRaises(VaultException):
            self.vault_manager.delete_recording(-1)
        
        # Test non-existent recording
        with self.assertRaises(VaultException):
            self.vault_manager.delete_recording(99999)
    
    def test_json_field_handling(self):
        """Test JSON field serialization and deserialization."""
        # Add recording with JSON fields
        key_points = ["Point 1", "Point 2", "Point 3"]
        tags = ["tag1", "tag2", "tag3"]
        
        recording_id = self.vault_manager.add_recording(
            filename="test.wav",
            key_points=key_points,
            tags=tags
        )
        
        # Retrieve and verify
        recordings = self.vault_manager.get_recordings()
        recording = recordings[0]
        
        self.assertEqual(recording['key_points'], key_points)
        self.assertEqual(recording['tags'], tags)
    
    def test_text_sanitization(self):
        """Test text input sanitization."""
        # Test with potentially problematic text
        problematic_text = "  Test\x00Text  "
        expected_clean = "TestText"
        
        recording_id = self.vault_manager.add_recording(
            filename="test.wav",
            title=problematic_text
        )
        
        recordings = self.vault_manager.get_recordings()
        self.assertEqual(recordings[0]['title'], expected_clean)
    
    def test_database_constraints(self):
        """Test database constraint enforcement."""
        # This should be enforced by our database schema
        with sqlite3.connect(self.vault_manager.db_path) as conn:
            # Test unique constraint on filename
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO recordings (filename) VALUES (?)",
                    ("test.wav",)
                )
                conn.execute(
                    "INSERT INTO recordings (filename) VALUES (?)",
                    ("test.wav",)
                )
    
    def test_database_migration(self):
        """Test database migration functionality."""
        # Create old-style database with archived column
        with sqlite3.connect(self.vault_manager.db_path) as conn:
            conn.execute("DROP TABLE IF EXISTS recordings")
            conn.execute("""
                CREATE TABLE recordings (
                    id INTEGER PRIMARY KEY,
                    filename TEXT UNIQUE NOT NULL,
                    title TEXT,
                    description TEXT,
                    category TEXT CHECK(category IN ('meeting', 'interview', 'lecture', 'note', 'other')) DEFAULT 'other',
                    duration REAL CHECK(duration >= 0) DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_size INTEGER CHECK(file_size >= 0) DEFAULT 0,
                    transcription TEXT,
                    summary TEXT,
                    key_points TEXT,
                    tags TEXT,
                    archived INTEGER DEFAULT 0
                )
            """)
            
            # Insert test data with archived recordings
            conn.execute(
                "INSERT INTO recordings (filename, archived) VALUES (?, ?)",
                ("active.wav", 0)
            )
            conn.execute(
                "INSERT INTO recordings (filename, archived) VALUES (?, ?)",
                ("archived.wav", 1)
            )
        
        # Reinitialize to trigger migration
        self.vault_manager._init_database()
        
        # Check that only non-archived recordings remain
        recordings = self.vault_manager.get_recordings()
        self.assertEqual(len(recordings), 1)
        self.assertEqual(recordings[0]['filename'], "active.wav")


if __name__ == '__main__':
    unittest.main()
