"""
Vault manager for ScribeVault recordings storage.

Handles SQLite database operations for recording metadata,
including CRUD operations with validation and sanitization.
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {"meeting", "interview", "lecture", "note", "other"}


class VaultException(Exception):
    """Exception raised for vault operation errors."""
    pass


class VaultManager:
    """Manages the recordings vault using SQLite storage."""

    def __init__(self, vault_dir: Optional[Path] = None):
        if vault_dir is None:
            vault_dir = Path("vault")
        self.vault_dir = Path(vault_dir)
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.vault_dir / "scribevault.db"
        self._init_database()

    def _init_database(self):
        """Initialize or migrate the database schema."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Check if table exists and needs migration
            cursor = conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='recordings'"
            )
            table_exists = cursor.fetchone() is not None

            if table_exists:
                # Check for archived column (old schema)
                cursor = conn.execute("PRAGMA table_info(recordings)")
                columns = {row[1] for row in cursor.fetchall()}
                if "archived" in columns:
                    self._migrate_from_archived(conn)
            else:
                self._create_table(conn)

    def _create_table(self, conn: sqlite3.Connection):
        """Create the recordings table."""
        conn.execute("""
            CREATE TABLE recordings (
                id INTEGER PRIMARY KEY,
                filename TEXT UNIQUE NOT NULL,
                title TEXT,
                description TEXT,
                category TEXT CHECK(category IN (
                    'meeting', 'interview', 'lecture', 'note', 'other'
                )) DEFAULT 'other',
                duration REAL CHECK(duration >= 0) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_size INTEGER CHECK(file_size >= 0) DEFAULT 0,
                transcription TEXT,
                summary TEXT,
                key_points TEXT,
                tags TEXT
            )
        """)

    def _migrate_from_archived(self, conn: sqlite3.Connection):
        """Migrate from old schema with archived column."""
        logger.info("Migrating database: removing archived column")

        # Keep only non-archived recordings
        conn.execute(
            "CREATE TABLE recordings_new AS "
            "SELECT id, filename, title, description, category, duration, "
            "created_at, file_size, transcription, summary, key_points, tags "
            "FROM recordings WHERE archived = 0"
        )
        conn.execute("DROP TABLE recordings")
        conn.execute("ALTER TABLE recordings_new RENAME TO recordings")

        # Re-apply constraints by recreating properly
        rows = conn.execute("SELECT * FROM recordings").fetchall()
        conn.execute("DROP TABLE recordings")
        self._create_table(conn)
        for row in rows:
            conn.execute(
                "INSERT INTO recordings "
                "(id, filename, title, description, category, duration, "
                "created_at, file_size, transcription, summary, "
                "key_points, tags) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                row,
            )

    @staticmethod
    def _sanitize_text(text: Optional[str]) -> Optional[str]:
        """Sanitize text input by stripping whitespace and null bytes."""
        if text is None:
            return None
        return text.replace("\x00", "").strip()

    @staticmethod
    def _normalize_category(category: Optional[str]) -> str:
        """Normalize category to a valid value, defaulting to 'other'."""
        if category and category in VALID_CATEGORIES:
            return category
        return "other"

    def add_recording(
        self,
        filename: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        category: str = "other",
        duration: float = 0.0,
        file_size: int = 0,
        transcription: Optional[str] = None,
        summary: Optional[str] = None,
        key_points: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        markdown_path: Optional[str] = None,
    ) -> int:
        """Add a recording to the vault.

        Returns the recording ID.
        Raises VaultException for validation errors.
        """
        # Validate filename
        if not filename or not filename.strip():
            raise VaultException("Filename cannot be empty")

        filename = filename.strip()

        # Sanitize text fields
        title = self._sanitize_text(title)
        description = self._sanitize_text(description)
        transcription = self._sanitize_text(transcription)
        summary = self._sanitize_text(summary)

        # Normalize category
        category = self._normalize_category(category)

        # Clamp negative values
        if duration < 0:
            duration = 0.0
        if file_size < 0:
            file_size = 0

        # Serialize JSON fields
        key_points_json = json.dumps(key_points) if key_points else None
        tags_json = json.dumps(tags) if tags else None

        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.execute(
                    "INSERT INTO recordings "
                    "(filename, title, description, category, duration, "
                    "file_size, transcription, summary, key_points, tags) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        filename, title, description, category,
                        duration, file_size, transcription, summary,
                        key_points_json, tags_json,
                    ),
                )
                recording_id = cursor.lastrowid
                logger.info(f"Added recording {recording_id}: {filename}")
                return recording_id
        except sqlite3.IntegrityError as e:
            raise VaultException(f"Recording already exists: {filename}") from e

    def get_recordings(
        self,
        category: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Retrieve recordings with optional filtering and pagination.

        Raises VaultException for invalid pagination parameters.
        """
        if limit is not None and limit < 0:
            raise VaultException("Limit cannot be negative")
        if offset < 0:
            raise VaultException("Offset cannot be negative")

        query = "SELECT * FROM recordings WHERE 1=1"
        params: list = []

        if category:
            query += " AND category = ?"
            params.append(category)

        if search_query:
            query += (
                " AND (title LIKE ? OR description LIKE ? "
                "OR transcription LIKE ? OR filename LIKE ?)"
            )
            like_param = f"%{search_query}%"
            params.extend([like_param] * 4)

        query += " ORDER BY created_at DESC"

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
            query += " OFFSET ?"
            params.append(offset)
        elif offset > 0:
            query += " LIMIT -1 OFFSET ?"
            params.append(offset)

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        return [self._row_to_dict(row) for row in rows]

    def get_recording_by_id(self, recording_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a single recording by ID."""
        if recording_id < 1:
            raise VaultException("Invalid recording ID")

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM recordings WHERE id = ?",
                (recording_id,),
            )
            row = cursor.fetchone()

        if row is None:
            return None
        return self._row_to_dict(row)

    def update_recording(
        self,
        recording_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        transcription: Optional[str] = None,
        summary: Optional[str] = None,
        key_points: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """Update a recording's metadata.

        Returns True on success.
        Raises VaultException for invalid IDs.
        """
        if recording_id < 1:
            raise VaultException("Invalid recording ID")

        # Verify recording exists
        existing = self.get_recording_by_id(recording_id)
        if existing is None:
            raise VaultException(
                f"Recording not found: {recording_id}"
            )

        updates = []
        params: list = []

        if title is not None:
            updates.append("title = ?")
            params.append(self._sanitize_text(title))
        if description is not None:
            updates.append("description = ?")
            params.append(self._sanitize_text(description))
        if category is not None:
            updates.append("category = ?")
            params.append(self._normalize_category(category))
        if transcription is not None:
            updates.append("transcription = ?")
            params.append(self._sanitize_text(transcription))
        if summary is not None:
            updates.append("summary = ?")
            params.append(self._sanitize_text(summary))
        if key_points is not None:
            updates.append("key_points = ?")
            params.append(json.dumps(key_points))
        if tags is not None:
            updates.append("tags = ?")
            params.append(json.dumps(tags))

        if not updates:
            return True

        params.append(recording_id)
        query = f"UPDATE recordings SET {', '.join(updates)} WHERE id = ?"

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute(query, params)

        logger.info(f"Updated recording {recording_id}")
        return True

    def delete_recording(self, recording_id: int) -> bool:
        """Delete a recording from the database.

        Returns True on success.
        Raises VaultException for invalid or non-existent IDs.
        """
        if recording_id < 1:
            raise VaultException("Invalid recording ID")

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.execute(
                "DELETE FROM recordings WHERE id = ?",
                (recording_id,),
            )
            if cursor.rowcount == 0:
                raise VaultException(
                    f"Recording not found: {recording_id}"
                )

        logger.info(f"Deleted recording {recording_id}")
        return True

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a database row to a dictionary with deserialized JSON fields."""
        d = dict(row)

        # Deserialize JSON fields
        for field in ("key_points", "tags"):
            value = d.get(field)
            if value and isinstance(value, str):
                try:
                    d[field] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    d[field] = []
            elif value is None:
                d[field] = []

        return d
