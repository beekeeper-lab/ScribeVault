"""
Vault manager for ScribeVault recording storage.

Provides SQLite-backed CRUD operations for recording metadata,
including pipeline status persistence.
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

VALID_CATEGORIES = ('meeting', 'interview', 'lecture', 'note', 'call', 'presentation', 'other')


class VaultException(Exception):
    """Exception raised by VaultManager operations."""
    pass


class VaultManager:
    """Manages recording metadata storage in SQLite."""

    def __init__(self, vault_dir: Optional[Path] = None):
        if vault_dir is None:
            vault_dir = Path("vault")
        self.vault_dir = Path(vault_dir)
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.vault_dir / "scribevault.db"
        self._init_database()

    def _init_database(self):
        """Initialize or migrate the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")

            # Check if recordings table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='recordings'"
            )
            table_exists = cursor.fetchone() is not None

            if table_exists:
                self._migrate_database(conn)
            else:
                self._create_tables(conn)

    def _create_tables(self, conn):
        """Create the database schema from scratch."""
        conn.execute("""
            CREATE TABLE recordings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE NOT NULL,
                title TEXT,
                description TEXT,
                category TEXT DEFAULT 'other',
                duration REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_size INTEGER DEFAULT 0,
                transcription TEXT,
                summary TEXT,
                key_points TEXT,
                tags TEXT,
                markdown_path TEXT,
                pipeline_status TEXT
            )
        """)

    def _migrate_database(self, conn):
        """Run migrations on existing database."""
        # Get current columns
        cursor = conn.execute("PRAGMA table_info(recordings)")
        columns = {row[1] for row in cursor.fetchall()}

        # Migration: remove archived column and archived rows
        if 'archived' in columns:
            conn.execute("DELETE FROM recordings WHERE archived = 1")
            # Recreate table without archived column
            conn.execute("ALTER TABLE recordings RENAME TO recordings_old")
            self._create_tables(conn)
            # Copy data (exclude archived column)
            old_cols = columns - {'archived'}
            # Only copy columns that exist in new schema
            new_cursor = conn.execute("PRAGMA table_info(recordings)")
            new_columns = {row[1] for row in new_cursor.fetchall()}
            shared = old_cols & new_columns
            col_list = ", ".join(sorted(shared))
            conn.execute(f"INSERT INTO recordings ({col_list}) SELECT {col_list} FROM recordings_old")
            conn.execute("DROP TABLE recordings_old")
            return

        # Migration: add pipeline_status column
        if 'pipeline_status' not in columns:
            conn.execute("ALTER TABLE recordings ADD COLUMN pipeline_status TEXT")

        # Migration: add markdown_path column
        if 'markdown_path' not in columns:
            conn.execute("ALTER TABLE recordings ADD COLUMN markdown_path TEXT")

    @staticmethod
    def _sanitize_text(text: Optional[str]) -> Optional[str]:
        """Sanitize text input by removing null bytes and stripping whitespace."""
        if text is None:
            return None
        # Remove null bytes and strip
        cleaned = text.replace('\x00', '').strip()
        return cleaned

    @staticmethod
    def _validate_category(category: Optional[str]) -> str:
        """Validate and normalize category."""
        if category and category in VALID_CATEGORIES:
            return category
        return 'other'

    def add_recording(self, filename: str, title: Optional[str] = None,
                      description: Optional[str] = None, category: Optional[str] = None,
                      duration: float = 0, file_size: int = 0,
                      transcription: Optional[str] = None, summary: Optional[str] = None,
                      key_points=None, tags=None, markdown_path: Optional[str] = None,
                      pipeline_status=None) -> int:
        """Add a new recording to the vault. Returns the recording ID."""
        # Validate filename
        clean_filename = self._sanitize_text(filename)
        if not clean_filename:
            raise VaultException("Filename cannot be empty")

        # Sanitize and validate
        title = self._sanitize_text(title)
        description = self._sanitize_text(description)
        category = self._validate_category(category)
        duration = max(0.0, float(duration)) if duration else 0.0
        file_size = max(0, int(file_size)) if file_size else 0

        # Serialize JSON fields
        key_points_json = json.dumps(key_points) if key_points else None
        tags_json = json.dumps(tags) if tags else None
        pipeline_status_json = json.dumps(pipeline_status) if pipeline_status else None

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    INSERT INTO recordings
                        (filename, title, description, category, duration, file_size,
                         transcription, summary, key_points, tags, markdown_path,
                         pipeline_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (clean_filename, title, description, category, duration, file_size,
                      transcription, summary, key_points_json, tags_json, markdown_path,
                      pipeline_status_json))
                return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            raise VaultException(f"Recording with filename '{clean_filename}' already exists") from e

    def get_recordings(self, category: Optional[str] = None,
                       search_query: Optional[str] = None,
                       limit: Optional[int] = None,
                       offset: Optional[int] = None) -> list:
        """Get recordings, optionally filtered."""
        if limit is not None and limit < 0:
            raise VaultException("Limit cannot be negative")
        if offset is not None and offset < 0:
            raise VaultException("Offset cannot be negative")

        query = "SELECT * FROM recordings WHERE 1=1"
        params = []

        if category:
            query += " AND category = ?"
            params.append(category)

        if search_query:
            query += " AND (title LIKE ? OR description LIKE ? OR transcription LIKE ?)"
            like_param = f"%{search_query}%"
            params.extend([like_param, like_param, like_param])

        query += " ORDER BY created_at DESC"

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        if offset is not None:
            if limit is None:
                query += " LIMIT -1"
            query += " OFFSET ?"
            params.append(offset)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()

        results = []
        for row in rows:
            record = dict(row)
            # Deserialize JSON fields
            if record.get('key_points'):
                try:
                    record['key_points'] = json.loads(record['key_points'])
                except (json.JSONDecodeError, TypeError):
                    record['key_points'] = None
            if record.get('tags'):
                try:
                    record['tags'] = json.loads(record['tags'])
                except (json.JSONDecodeError, TypeError):
                    record['tags'] = None
            if record.get('pipeline_status'):
                try:
                    record['pipeline_status'] = json.loads(record['pipeline_status'])
                except (json.JSONDecodeError, TypeError):
                    record['pipeline_status'] = None
            results.append(record)

        return results

    def update_recording(self, recording_id: int, **fields) -> bool:
        """Update recording fields. Returns True on success."""
        if recording_id is None or recording_id < 0:
            raise VaultException("Invalid recording ID")

        # Check recording exists
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT id FROM recordings WHERE id = ?", (recording_id,)
            ).fetchone()
            if not row:
                raise VaultException(f"Recording {recording_id} not found")

        # Sanitize fields
        if 'title' in fields:
            fields['title'] = self._sanitize_text(fields['title'])
        if 'description' in fields:
            fields['description'] = self._sanitize_text(fields['description'])
        if 'category' in fields:
            fields['category'] = self._validate_category(fields['category'])
        if 'duration' in fields:
            fields['duration'] = max(0.0, float(fields['duration']))
        if 'file_size' in fields:
            fields['file_size'] = max(0, int(fields['file_size']))
        if 'key_points' in fields and not isinstance(fields['key_points'], str):
            fields['key_points'] = json.dumps(fields['key_points'])
        if 'tags' in fields and not isinstance(fields['tags'], str):
            fields['tags'] = json.dumps(fields['tags'])
        if 'pipeline_status' in fields and not isinstance(fields['pipeline_status'], str):
            fields['pipeline_status'] = json.dumps(fields['pipeline_status'])

        if not fields:
            return True

        set_clauses = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [recording_id]

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"UPDATE recordings SET {set_clauses} WHERE id = ?", values
            )

        return True

    def delete_recording(self, recording_id: int) -> bool:
        """Delete a recording. Returns True on success."""
        if recording_id is None or recording_id < 0:
            raise VaultException("Invalid recording ID")

        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT id FROM recordings WHERE id = ?", (recording_id,)
            ).fetchone()
            if not row:
                raise VaultException(f"Recording {recording_id} not found")

            conn.execute("DELETE FROM recordings WHERE id = ?", (recording_id,))

        return True
