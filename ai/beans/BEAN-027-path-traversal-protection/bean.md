# BEAN-027: Path Traversal Protection for Database-Sourced Paths

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-027     |
| Title     | Path Traversal Protection for Database-Sourced Paths |
| Type      | bug-fix      |
| Priority  | P1           |
| Status    | Done         |
| Created   | 2026-02-10   |
| Started   |              |
| Completed |              |
| Duration  |              |

## Problem Statement

Several file operations use paths loaded from the SQLite database without validating that they resolve within expected directories. If the database were tampered with (e.g., a crafted `filename` containing `../../../etc/passwd`), the application could read, copy, or open arbitrary files on the filesystem. Affected operations include: audio playback via `xdg-open` (`qt_vault_dialog.py:1068`), recording export via `shutil.copy2` (`qt_vault_dialog.py:791`), markdown file reading (`qt_summary_viewer.py:853`), and vault folder opening (`qt_vault_dialog.py:1019`).

## Goal

All file operations that use database-sourced paths validate that the resolved path is within the expected directory before proceeding, preventing path traversal attacks.

## Scope

### In Scope

- Add a shared path validation utility that checks `Path.resolve()` is a child of the expected base directory
- Apply validation to: audio file playback, recording export, markdown file read, vault folder open
- Return a clear error message to the user when a path fails validation

### Out of Scope

- Database integrity checks or tamper detection
- Encrypting the database
- Validating paths for files the user selects via file dialogs (those are user-chosen, not DB-sourced)

## Acceptance Criteria

- [x] A shared `validate_path_within(path, base_dir)` utility exists and is used for all DB-sourced file operations
- [x] Audio playback (`qt_vault_dialog.py`) validates the filename resolves within `recordings/`
- [x] Export operations (`qt_vault_dialog.py`) validate source and destination paths
- [x] Markdown reading (`qt_summary_viewer.py`) validates the path resolves within `summaries/`
- [x] Each validation failure shows a user-facing error and logs a warning
- [x] Unit tests cover: valid paths pass, `..` traversal blocked, symlink traversal blocked, absolute path injection blocked
- [x] `pytest tests/` passes, `flake8 src/ tests/` is clean

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Create path validation utility | Developer | | DONE |
| 2 | Apply validation to vault dialog file operations | Developer | 1 | DONE |
| 3 | Apply validation to summary viewer file operations | Developer | 1 | DONE |
| 4 | Write unit tests for path validation | Tech QA | 2, 3 | DONE |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

Key files: `src/gui/qt_vault_dialog.py` (lines 791, 1019, 1068), `src/gui/qt_summary_viewer.py` (lines 853, 1107). The `resolve()` + `is_relative_to()` pattern (Python 3.9+) is the recommended approach.
