"""
Vault manager for ScribeVault recording storage.

Manages a SQLite database of recordings with metadata, transcriptions,
and AI summaries.
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {"meeting", "interview", "lecture", "note", "other"}


class VaultException(Exception):
    """Exception raised for vault operations."""
    pass


class VaultManager:
    """Manages recording storage in a SQLite vault database."""

    def __init__(self, vault_dir: Optional[Path] = None):
        """Initialize the vault manager.

        Args:
            vault_dir: Directory for the vault database. Defaults to 'vault/'.
        """
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

            # Check if table exists and has the old 'archived' column
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='recordings'"
            )
            table_exists = cursor.fetchone() is not None

            if table_exists:
                # Check for archived column (old schema)
                columns = [
                    row[1]
                    for row in conn.execute("PRAGMA table_info(recordings)")
                ]
                if "archived" in columns:
                    self._migrate_remove_archived(conn)
                    # Re-read columns after migration
                    columns = [
                        row[1]
                        for row in conn.execute("PRAGMA table_info(recordings)")
                    ]
                # Check if markdown_path column exists, add if missing
                if "markdown_path" not in columns:
                    conn.execute(
                        "ALTER TABLE recordings ADD COLUMN markdown_path TEXT"
                    )
            else:
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
                        markdown_path TEXT
                    )
                """)

    def _migrate_remove_archived(self, conn: sqlite3.Connection):
        """Migrate database by removing archived column and archived rows."""
        logger.info("Migrating database: removing archived column")
        # Delete archived recordings
        conn.execute("DELETE FROM recordings WHERE archived = 1")
        # Recreate table without archived column
        conn.execute("""
            CREATE TABLE recordings_new (
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
                markdown_path TEXT
            )
        """)
        conn.execute("""
            INSERT INTO recordings_new
                (id, filename, title, description, category, duration,
                 created_at, file_size, transcription, summary, key_points, tags)
            SELECT id, filename, title, description, category, duration,
                   created_at, file_size, transcription, summary, key_points, tags
            FROM recordings
        """)
        conn.execute("DROP TABLE recordings")
        conn.execute("ALTER TABLE recordings_new RENAME TO recordings")

    @staticmethod
    def _sanitize_text(text: Optional[str]) -> Optional[str]:
        """Sanitize text input by stripping whitespace and null bytes."""
        if text is None:
            return None
        return text.replace("\x00", "").strip()

    @staticmethod
    def _validate_category(category: Optional[str]) -> str:
        """Validate and normalize category, defaulting to 'other'."""
        if category and category in VALID_CATEGORIES:
            return category
        return "other"

    def add_recording(
        self,
        filename: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        duration: float = 0.0,
        file_size: int = 0,
        transcription: Optional[str] = None,
        summary: Optional[str] = None,
        key_points: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        markdown_path: Optional[str] = None,
    ) -> int:
        """Add a recording to the vault.

        Args:
            filename: Audio filename (must be unique).
            title: Recording title.
            description: Recording description.
            category: Category (meeting, interview, lecture, note, other).
            duration: Duration in seconds.
            file_size: File size in bytes.
            transcription: Transcription text.
            summary: AI summary text.
            key_points: List of key points.
            tags: List of tags.
            markdown_path: Path to markdown summary file.

        Returns:
            The new recording's ID.

        Raises:
            VaultException: If filename is empty or duplicate.
        """
        filename = self._sanitize_text(filename)
        if not filename:
            raise VaultException("Filename cannot be empty")

        title = self._sanitize_text(title)
        description = self._sanitize_text(description)
        category = self._validate_category(category)
        duration = max(0.0, duration) if duration else 0.0
        file_size = max(0, file_size) if file_size else 0

        key_points_json = json.dumps(key_points) if key_points else None
        tags_json = json.dumps(tags) if tags else None

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO recordings
                        (filename, title, description, category, duration,
                         file_size, transcription, summary, key_points, tags,
                         markdown_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        filename,
                        title,
                        description,
                        category,
                        duration,
                        file_size,
                        transcription,
                        summary,
                        key_points_json,
                        tags_json,
                        markdown_path,
                    ),
                )
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise VaultException(
                f"Recording with filename '{filename}' already exists"
            )

    def get_recordings(
        self,
        category: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get recordings from the vault.

        Args:
            category: Filter by category.
            search_query: Search in title, description, transcription.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of recording dictionaries.

        Raises:
            VaultException: If pagination parameters are invalid.
        """
        if limit is not None and limit < 0:
            raise VaultException("Limit must be non-negative")
        if offset < 0:
            raise VaultException("Offset must be non-negative")

        query = "SELECT * FROM recordings"
        params: list = []
        conditions: list = []

        if category:
            conditions.append("category = ?")
            params.append(category)

        if search_query:
            conditions.append(
                "(title LIKE ? OR description LIKE ? OR transcription LIKE ?)"
            )
            like_param = f"%{search_query}%"
            params.extend([like_param, like_param, like_param])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY created_at DESC"

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
            if offset > 0:
                query += " OFFSET ?"
                params.append(offset)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()

        return [self._row_to_dict(row) for row in rows]

    def update_recording(
        self,
        recording_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        transcription: Optional[str] = None,
        summary: Optional[str] = None,
    ) -> bool:
        """Update a recording in the vault.

        Args:
            recording_id: ID of the recording to update.
            title: New title (None to skip).
            description: New description (None to skip).
            category: New category (None to skip).
            transcription: New transcription (None to skip).
            summary: New summary (None to skip).

        Returns:
            True if update was successful.

        Raises:
            VaultException: If recording_id is invalid or not found.
        """
        if recording_id < 1:
            raise VaultException("Invalid recording ID")

        # Check recording exists
        with sqlite3.connect(self.db_path) as conn:
            exists = conn.execute(
                "SELECT id FROM recordings WHERE id = ?", (recording_id,)
            ).fetchone()
            if not exists:
                raise VaultException(
                    f"Recording with ID {recording_id} not found"
                )

        updates: list = []
        params: list = []

        if title is not None:
            updates.append("title = ?")
            params.append(self._sanitize_text(title))
        if description is not None:
            updates.append("description = ?")
            params.append(self._sanitize_text(description))
        if category is not None:
            updates.append("category = ?")
            params.append(self._validate_category(category))
        if transcription is not None:
            updates.append("transcription = ?")
            params.append(transcription)
        if summary is not None:
            updates.append("summary = ?")
            params.append(summary)

        if not updates:
            return True  # Nothing to update

        params.append(recording_id)
        query = f"UPDATE recordings SET {', '.join(updates)} WHERE id = ?"

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(query, params)

        return True

    def delete_recording(self, recording_id: int) -> bool:
        """Delete a recording from the vault.

        Args:
            recording_id: ID of the recording to delete.

        Returns:
            True if deletion was successful.

        Raises:
            VaultException: If recording_id is invalid or not found.
        """
        if recording_id < 1:
            raise VaultException("Invalid recording ID")

        with sqlite3.connect(self.db_path) as conn:
            exists = conn.execute(
                "SELECT id FROM recordings WHERE id = ?", (recording_id,)
            ).fetchone()
            if not exists:
                raise VaultException(
                    f"Recording with ID {recording_id} not found"
                )

            conn.execute(
                "DELETE FROM recordings WHERE id = ?", (recording_id,)
            )

        return True

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a database row to a dictionary with JSON deserialization."""
        d = dict(row)
        # Deserialize JSON fields
        for field in ("key_points", "tags"):
            if d.get(field):
                try:
                    d[field] = json.loads(d[field])
                except (json.JSONDecodeError, TypeError):
                    d[field] = None
        return d
