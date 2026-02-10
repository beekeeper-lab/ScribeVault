"""
Vault manager for ScribeVault recordings database.
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

VALID_CATEGORIES = ("meeting", "interview", "lecture", "note", "other")


class VaultException(Exception):
    """Exception raised for vault operations."""
    pass


class VaultManager:
    """Manages the recordings vault backed by SQLite."""

    def __init__(self, vault_dir: Optional[Path] = None):
        if vault_dir is None:
            vault_dir = Path.home() / ".scribevault"
        self.vault_dir = Path(vault_dir)
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.vault_dir / "scribevault.db"
        self._init_database()

    def _init_database(self):
        """Initialize or migrate the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")

            # Check if table exists and needs migration
            cursor = conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='recordings'"
            )
            table_exists = cursor.fetchone() is not None

            if table_exists:
                self._migrate_if_needed(conn)
            else:
                self._create_table(conn)

    def _create_table(self, conn):
        """Create the recordings table."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS recordings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE NOT NULL,
                title TEXT,
                description TEXT,
                category TEXT DEFAULT 'other',
                duration REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_size INTEGER DEFAULT 0,
                transcription TEXT,
                original_transcription TEXT,
                summary TEXT,
                key_points TEXT,
                tags TEXT,
                markdown_path TEXT
            )
        """)

    def _migrate_if_needed(self, conn):
        """Run migrations on existing database."""
        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(recordings)")
        }

        # Migration: remove archived column
        if "archived" in columns:
            conn.execute(
                "DELETE FROM recordings WHERE archived = 1"
            )
            self._rebuild_without_column(conn, "archived")
            # Refresh columns after rebuild
            columns = {
                row[1]
                for row in conn.execute("PRAGMA table_info(recordings)")
            }

        # Migration: add original_transcription column
        if "original_transcription" not in columns:
            conn.execute(
                "ALTER TABLE recordings "
                "ADD COLUMN original_transcription TEXT"
            )

        # Migration: add markdown_path column
        if "markdown_path" not in columns:
            conn.execute(
                "ALTER TABLE recordings "
                "ADD COLUMN markdown_path TEXT"
            )

    def _rebuild_without_column(self, conn, column_name):
        """Rebuild table without a specific column (SQLite limitation)."""
        # Get current columns minus the one to remove
        columns_info = conn.execute("PRAGMA table_info(recordings)").fetchall()
        keep_columns = [
            col[1] for col in columns_info if col[1] != column_name
        ]
        cols = ", ".join(keep_columns)

        conn.execute(
            f"CREATE TABLE recordings_new AS "
            f"SELECT {cols} FROM recordings"
        )
        conn.execute("DROP TABLE recordings")
        conn.execute("ALTER TABLE recordings_new RENAME TO recordings")

    @staticmethod
    def _sanitize_text(text: Optional[str]) -> Optional[str]:
        """Strip whitespace and remove null bytes from text."""
        if text is None:
            return None
        return text.strip().replace("\x00", "")

    @staticmethod
    def _validate_category(category: Optional[str]) -> str:
        """Validate and normalize category."""
        if category and category in VALID_CATEGORIES:
            return category
        return "other"

    def add_recording(
        self,
        filename: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        duration: float = 0,
        file_size: int = 0,
        transcription: Optional[str] = None,
        summary: Optional[str] = None,
        key_points: Optional[list] = None,
        tags: Optional[list] = None,
        markdown_path: Optional[str] = None,
    ) -> int:
        """Add a new recording to the vault.

        Returns:
            The new recording's ID.

        Raises:
            VaultException on validation failure or duplicate filename.
        """
        filename = self._sanitize_text(filename)
        if not filename:
            raise VaultException("Filename is required and cannot be empty.")

        title = self._sanitize_text(title)
        description = self._sanitize_text(description)
        category = self._validate_category(category)
        duration = max(0.0, float(duration)) if duration else 0.0
        file_size = max(0, int(file_size)) if file_size else 0

        key_points_json = json.dumps(key_points) if key_points else None
        tags_json = json.dumps(tags) if tags else None

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO recordings
                        (filename, title, description, category, duration,
                         file_size, transcription, summary, key_points,
                         tags, markdown_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        filename, title, description, category, duration,
                        file_size, transcription, summary, key_points_json,
                        tags_json, markdown_path,
                    ),
                )
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise VaultException(
                f"Recording with filename '{filename}' already exists."
            )

    def get_recordings(
        self,
        category: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict]:
        """Retrieve recordings from the vault.

        Raises:
            VaultException on invalid pagination parameters.
        """
        if limit is not None and limit < 0:
            raise VaultException("Limit must be non-negative.")
        if offset is not None and offset < 0:
            raise VaultException("Offset must be non-negative.")

        query = "SELECT * FROM recordings WHERE 1=1"
        params: list = []

        if category:
            query += " AND category = ?"
            params.append(category)

        if search_query:
            query += (
                " AND (title LIKE ? OR description LIKE ? "
                "OR filename LIKE ? OR transcription LIKE ?)"
            )
            like = f"%{search_query}%"
            params.extend([like, like, like, like])

        query += " ORDER BY created_at DESC"

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        if offset is not None:
            query += " OFFSET ?"
            params.append(offset)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()

        return [self._row_to_dict(row) for row in rows]

    def update_recording(self, recording_id: int, **kwargs) -> bool:
        """Update fields on an existing recording.

        Raises:
            VaultException on invalid ID or non-existent recording.
        """
        if recording_id is None or recording_id < 0:
            raise VaultException("Invalid recording ID.")

        # Verify existence
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT id FROM recordings WHERE id = ?",
                (recording_id,),
            ).fetchone()
            if not row:
                raise VaultException(
                    f"Recording {recording_id} not found."
                )

        allowed = {
            "title", "description", "category", "duration",
            "file_size", "transcription", "original_transcription",
            "summary", "key_points", "tags", "markdown_path",
        }
        updates = {}
        for key, value in kwargs.items():
            if key not in allowed:
                continue
            if key == "category":
                value = self._validate_category(value)
            if key in ("key_points", "tags") and isinstance(value, list):
                value = json.dumps(value)
            if key in ("title", "description") and isinstance(value, str):
                value = self._sanitize_text(value)
            updates[key] = value

        if not updates:
            return True

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [recording_id]

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"UPDATE recordings SET {set_clause} WHERE id = ?",
                values,
            )
        return True

    def delete_recording(self, recording_id: int) -> bool:
        """Delete a recording from the vault.

        Raises:
            VaultException on invalid ID or non-existent recording.
        """
        if recording_id is None or recording_id < 0:
            raise VaultException("Invalid recording ID.")

        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT id FROM recordings WHERE id = ?",
                (recording_id,),
            ).fetchone()
            if not row:
                raise VaultException(
                    f"Recording {recording_id} not found."
                )
            conn.execute(
                "DELETE FROM recordings WHERE id = ?",
                (recording_id,),
            )
        return True

    def _row_to_dict(self, row) -> Dict:
        """Convert a database row to a dictionary."""
        d = dict(row)
        # Deserialize JSON fields
        for field in ("key_points", "tags"):
            if d.get(field) and isinstance(d[field], str):
                try:
                    d[field] = json.loads(d[field])
                except (json.JSONDecodeError, TypeError):
                    d[field] = None
        return d
