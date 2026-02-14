"""
Shared formatting and platform utility functions for ScribeVault.

Consolidates duplicated helpers (duration/size formatting, date parsing,
platform file-open) into a single module.
"""

import os
import platform
import subprocess
import logging
from datetime import datetime
from typing import Optional, Union

logger = logging.getLogger(__name__)


def format_duration(seconds: float, style: str = "compact") -> str:
    """Format duration in seconds to a human-readable string.

    Args:
        seconds: Duration in seconds.
        style: ``"compact"`` for ``M:SS`` (UI tables) or
               ``"descriptive"`` for ``Xh Xm Xs`` (exports).

    Returns:
        Formatted duration string.
    """
    if not seconds or seconds <= 0:
        if style == "descriptive":
            return "Unknown"
        return "0:00"

    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if style == "descriptive":
        if hrs > 0:
            return f"{hrs}h {mins}m {secs}s"
        elif mins > 0:
            return f"{mins}m {secs}s"
        return f"{secs}s"

    # compact  –  M:SS
    total_mins = int(seconds // 60)
    remaining = int(seconds % 60)
    return f"{total_mins}:{remaining:02d}"


def format_file_size(bytes_size: Union[int, float]) -> str:
    """Format a file size to a human-readable string.

    Returns values like ``"1.2 MB"`` or ``"0 B"``.
    """
    if not bytes_size or bytes_size <= 0:
        return "0 B"

    size = float(bytes_size)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def parse_datetime(
    value: Optional[Union[str, datetime]],
) -> Optional[datetime]:
    """Parse an ISO-8601 date string (with optional trailing ``Z``)
    into a :class:`datetime`.

    If *value* is already a :class:`datetime`, return it unchanged.
    Returns ``None`` when the value cannot be parsed.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError, AttributeError):
        return None


def open_with_system_app(path: Union[str, "os.PathLike[str]"]) -> None:
    """Open *path* with the platform's default application.

    Raises :class:`OSError` on failure.
    """
    path_str = str(path)
    system = platform.system()
    if system == "Windows":
        os.startfile(path_str)  # type: ignore[attr-defined]
    elif system == "Darwin":
        subprocess.run(["open", path_str], check=True)
    else:
        subprocess.run(["xdg-open", path_str], check=True)
