"""
Vault management for ScribeVault recordings database.
"""

import sqlite3
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

VALID_CATEGORIES = ["meeting", "interview", "lecture", "note", "other"]


class VaultException(Exception):
    """Custom exception for vault operations."""

    pass


class VaultManager:
    """Manages the recordings vault database."""

    def __init__(self, vault_dir: str = "vault"):
        self.vault_dir = Path(vault_dir)
        self.vault_dir.mkdir(exist_ok=True)
        self.db_path = self.vault_dir / "scribevault.db"
        self._lock = threading.Lock()
        self._init_database()

    def _init_database(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Check if table exists and needs migration
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='recordings'")
            table_exists = cursor.fetchone() is not None

            if table_exists:
                self._migrate_database(conn)
            else:
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
                        tags TEXT,
                        summary_history TEXT,
                        markdown_path TEXT
                    )
                """)

    def _migrate_database(self, conn):
        """Handle database migration from older schemas."""
        # Check for archived column (old schema)
        cursor = conn.execute("PRAGMA table_info(recordings)")
        columns = {row[1]: row for row in cursor.fetchall()}

        if "archived" in columns:
            # Delete archived recordings, then recreate without archived column
            conn.execute("DELETE FROM recordings WHERE archived = 1")

            # Get remaining data
            rows = conn.execute("SELECT * FROM recordings WHERE archived = 0").fetchall()
            col_names = [desc[0] for desc in conn.execute("SELECT * FROM recordings LIMIT 0").description]

            conn.execute("DROP TABLE recordings")
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
                    tags TEXT,
                    summary_history TEXT,
                    markdown_path TEXT
                )
            """)

            # Re-insert non-archived data
            for row in rows:
                row_dict = dict(zip(col_names, row))
                conn.execute(
                    """INSERT INTO recordings (id, filename, title, description, category,
                       duration, created_at, file_size, transcription, summary, key_points, tags)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        row_dict.get("id"),
                        row_dict.get("filename"),
                        row_dict.get("title"),
                        row_dict.get("description"),
                        row_dict.get("category", "other"),
                        row_dict.get("duration", 0),
                        row_dict.get("created_at"),
                        row_dict.get("file_size", 0),
                        row_dict.get("transcription"),
                        row_dict.get("summary"),
                        row_dict.get("key_points"),
                        row_dict.get("tags"),
                    ),
                )

        # Add summary_history column if missing
        if "summary_history" not in columns:
            try:
                conn.execute("ALTER TABLE recordings ADD COLUMN summary_history TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists

        # Add markdown_path column if missing
        if "markdown_path" not in columns:
            try:
                conn.execute("ALTER TABLE recordings ADD COLUMN markdown_path TEXT")
            except sqlite3.OperationalError:
                pass

    @staticmethod
    def _sanitize_text(text: Optional[str]) -> Optional[str]:
        """Sanitize text input by removing null bytes and extra whitespace."""
        if text is None:
            return None
        # Remove null bytes
        text = text.replace("\x00", "")
        # Strip leading/trailing whitespace
        text = text.strip()
        return text if text else None

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
    ) -> int:
        """Add a recording to the vault.

        Returns:
            The recording ID.

        Raises:
            VaultException: If validation fails or database error occurs.
        """
        # Validate filename
        filename = self._sanitize_text(filename)
        if not filename:
            raise VaultException("Filename cannot be empty")

        # Sanitize text fields
        title = self._sanitize_text(title)
        description = self._sanitize_text(description)
        transcription = self._sanitize_text(transcription)
        summary = self._sanitize_text(summary)

        # Validate and correct category
        if category not in VALID_CATEGORIES:
            category = "other"

        # Correct negative values
        if duration < 0:
            duration = 0.0
        if file_size < 0:
            file_size = 0

        # Serialize JSON fields
        key_points_json = json.dumps(key_points) if key_points else None
        tags_json = json.dumps(tags) if tags else None

        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("PRAGMA foreign_keys = ON")
                    cursor = conn.execute(
                        """INSERT INTO recordings
                           (filename, title, description, category, duration,
                            file_size, transcription, summary, key_points, tags)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
                        ),
                    )
                    return cursor.lastrowid
            except sqlite3.IntegrityError as e:
                raise VaultException(f"Recording already exists: {e}")
            except sqlite3.Error as e:
                raise VaultException(f"Database error: {e}")

    def get_recordings(
        self,
        category: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get recordings with optional filtering.

        Raises:
            VaultException: If pagination values are invalid.
        """
        if limit is not None and limit < 0:
            raise VaultException("Limit cannot be negative")
        if offset is not None and offset < 0:
            raise VaultException("Offset cannot be negative")

        query = "SELECT * FROM recordings"
        params: list = []
        conditions = []

        if category:
            conditions.append("category = ?")
            params.append(category)

        if search_query:
            conditions.append("(title LIKE ? OR description LIKE ? OR filename LIKE ?)")
            pattern = f"%{search_query}%"
            params.extend([pattern, pattern, pattern])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY created_at DESC"

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        if offset is not None:
            query += " OFFSET ?"
            params.append(offset)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()

        return [self._row_to_dict(row) for row in rows]

    def update_recording(self, recording_id: int, **kwargs) -> bool:
        """Update a recording by ID.

        Raises:
            VaultException: If recording not found or invalid ID.
        """
        if recording_id < 1:
            raise VaultException("Invalid recording ID")

        # Check existence
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            row = conn.execute("SELECT id FROM recordings WHERE id = ?", (recording_id,)).fetchone()
            if not row:
                raise VaultException(f"Recording not found: {recording_id}")

        # Validate category if provided
        if "category" in kwargs and kwargs["category"] not in VALID_CATEGORIES:
            kwargs["category"] = "other"

        # Sanitize text fields
        for field in ("title", "description", "transcription", "summary"):
            if field in kwargs and kwargs[field] is not None:
                kwargs[field] = self._sanitize_text(kwargs[field])

        # Serialize JSON fields
        for field in ("key_points", "tags", "summary_history"):
            if field in kwargs and kwargs[field] is not None:
                kwargs[field] = json.dumps(kwargs[field])

        if not kwargs:
            return True

        set_clause = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [recording_id]

        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute(
                    f"UPDATE recordings SET {set_clause} WHERE id = ?",
                    values,
                )
        return True

    def delete_recording(self, recording_id: int) -> bool:
        """Delete a recording by ID.

        Raises:
            VaultException: If recording not found or invalid ID.
        """
        if recording_id < 1:
            raise VaultException("Invalid recording ID")

        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                row = conn.execute("SELECT id FROM recordings WHERE id = ?", (recording_id,)).fetchone()
                if not row:
                    raise VaultException(f"Recording not found: {recording_id}")

                conn.execute("DELETE FROM recordings WHERE id = ?", (recording_id,))
        return True

    def add_summary(
        self,
        recording_id: int,
        content: str,
        template_name: str = "",
        prompt_used: str = "",
    ) -> bool:
        """Add a new summary to a recording's history.

        Updates both the main summary field and the summary_history JSON list.

        Args:
            recording_id: The recording to update
            content: Summary text content
            template_name: Name of the template used (or empty for custom)
            prompt_used: The actual prompt text used

        Returns:
            True on success

        Raises:
            VaultException: If recording not found.
        """
        if recording_id < 1:
            raise VaultException("Invalid recording ID")

        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT summary_history FROM recordings WHERE id = ?",
                    (recording_id,),
                ).fetchone()
                if not row:
                    raise VaultException(f"Recording not found: {recording_id}")

                # Load existing history
                history_json = row["summary_history"]
                history = json.loads(history_json) if history_json else []

                # Append new entry
                entry = {
                    "content": content,
                    "template_name": template_name,
                    "prompt_used": prompt_used,
                    "created_at": datetime.now().isoformat(),
                }
                history.append(entry)

                # Update both summary and summary_history
                conn.execute(
                    "UPDATE recordings SET summary = ?, summary_history = ? WHERE id = ?",
                    (content, json.dumps(history), recording_id),
                )
        return True

    @staticmethod
    def _row_to_dict(row) -> Dict[str, Any]:
        """Convert a database row to a dictionary."""
        d = dict(row)

        # Deserialize JSON fields
        for field in ("key_points", "tags"):
            if d.get(field):
                try:
                    d[field] = json.loads(d[field])
                except (json.JSONDecodeError, TypeError):
                    d[field] = []
            else:
                d[field] = []

        # Deserialize summary_history
        if d.get("summary_history"):
            try:
                d["summary_history"] = json.loads(d["summary_history"])
            except (json.JSONDecodeError, TypeError):
                d["summary_history"] = []
        else:
            d["summary_history"] = []

        return d
