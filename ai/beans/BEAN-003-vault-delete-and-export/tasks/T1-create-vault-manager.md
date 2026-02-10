# T1: Create VaultManager Module

## Owner: developer

## Depends On: (none)

## Status: DONE

## Description

Create the `src/vault/` package with `__init__.py` and `manager.py`. Implement the `VaultManager` class with full CRUD operations including `delete_recording()`. The class is already imported by `qt_vault_dialog.py`, `qt_main_window.py`, `qt_app.py`, and `main_window.py` but does not exist yet.

## Acceptance Criteria

- [ ] `src/vault/__init__.py` exists
- [ ] `src/vault/manager.py` implements VaultManager class with VaultException
- [ ] SQLite database with recordings table (id, filename, title, description, category, duration, created_at, file_size, transcription, summary, key_points, tags)
- [ ] `add_recording()` with validation (empty filename, duplicate, category correction, negative values, text sanitization)
- [ ] `get_recordings()` with filtering (category, search_query) and pagination (limit, offset)
- [ ] `update_recording()` with validation
- [ ] `delete_recording(recording_id)` removes database entry
- [ ] JSON field serialization/deserialization for key_points and tags
- [ ] Database migration from old schema with archived column
- [ ] All existing tests in `test_vault_manager.py` pass

## Files to Create/Modify

- Create: `src/vault/__init__.py`
- Create: `src/vault/manager.py`
