# Task 001: Remove CustomTkinter GUI Files

## Metadata

| Field | Value |
|-------|-------|
| Task ID | BEAN-012-T001 |
| Owner | developer |
| Status | Done |
| Depends On | — |

## Description

Remove the CustomTkinter-specific GUI source files that are no longer needed now that PySide6 is the sole GUI framework.

## Files to Remove

- `src/gui/main_window.py` (1,645 lines - CustomTkinter main window)
- `src/gui/settings_window.py` (857 lines - CustomTkinter settings dialog)
- `src/gui/assets.py` (99 lines - CustomTkinter asset manager using ctk.CTkImage)
- `src/gui/archive_window.py` (empty file - unused CustomTkinter placeholder)

## Acceptance Criteria

- [ ] All four files are deleted from the repository
- [ ] No dangling imports reference these deleted files
- [ ] `src/gui/__init__.py` does not reference any deleted modules
