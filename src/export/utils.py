"""
Shared export utilities for ScribeVault.

Provides common filename sanitization, directory creation helpers,
and path validation used across vault export, markdown generation,
and transcription export.
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def validate_path_within(path: Path, base_dir: Path) -> Path:
    """Validate that a resolved path is within the expected base directory.

    Resolves both paths to absolute form and checks that the target
    is a child of base_dir. This prevents path traversal attacks via
    ``..`` sequences, symlinks, or absolute path injection.

    Args:
        path: The path to validate (may be relative or absolute).
        base_dir: The directory that path must be within.

    Returns:
        The resolved absolute path.

    Raises:
        ValueError: If the resolved path is not within base_dir.
    """
    resolved = path.resolve()
    base = base_dir.resolve()
    if not (resolved == base or str(resolved).startswith(str(base) + "/")):
        raise ValueError(
            f"Path traversal blocked: {path} resolves to "
            f"{resolved}, which is outside {base}"
        )
    return resolved


def sanitize_title(title: str, max_length: int = 50) -> str:
    """Sanitize a recording title for use as a filename or directory name.

    Keeps alphanumeric characters, spaces, hyphens, and underscores.
    Replaces spaces with underscores. Truncates to max_length.

    Args:
        title: Raw title string.
        max_length: Maximum length of the result (default 50).

    Returns:
        A filesystem-safe string derived from the title.
        Returns 'Untitled' if the title is empty after sanitization.
    """
    safe = "".join(
        c for c in title if c.isalnum() or c in (" ", "-", "_")
    ).strip()
    safe = safe.replace(" ", "_")[:max_length]
    return safe if safe else "Untitled"


def secure_mkdir(path: Path, mode: int = 0o700) -> Path:
    """Create a directory with restrictive permissions.

    On POSIX systems, sets the directory permissions to *mode*
    (default ``0o700`` — owner-only access).  On non-POSIX
    platforms the call is a no-op after creating the directory.

    Args:
        path: Directory to create.
        mode: POSIX permission bits (default 0o700).

    Returns:
        The created (or existing) directory Path.
    """
    path.mkdir(parents=True, exist_ok=True)
    if os.name == "posix":
        path.chmod(mode)
    return path


def secure_file_permissions(path: Path, mode: int = 0o600):
    """Set restrictive permissions on a file.

    On POSIX systems, sets file permissions to *mode*
    (default ``0o600`` — owner read/write only).
    No-op on non-POSIX platforms.

    Args:
        path: File to chmod.
        mode: POSIX permission bits (default 0o600).
    """
    if os.name == "posix" and path.exists():
        path.chmod(mode)


def create_unique_subfolder(parent: Path, name: str) -> Path:
    """Create a uniquely-named subfolder under parent.

    If ``parent/name`` already exists, appends ``_2``, ``_3``, etc.
    until a free name is found.

    Args:
        parent: Parent directory (must already exist).
        name: Desired subfolder name.

    Returns:
        The Path of the created directory.
    """
    candidate = parent / name
    if not candidate.exists():
        return secure_mkdir(candidate)

    counter = 2
    while True:
        candidate = parent / f"{name}_{counter}"
        if not candidate.exists():
            return secure_mkdir(candidate)
        counter += 1
