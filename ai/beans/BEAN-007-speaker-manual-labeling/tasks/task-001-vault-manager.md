# Task 001: Implement VaultManager Module

## Metadata

| Field | Value |
|-------|-------|
| Task ID | BEAN-007-T001 |
| Owner | developer |
| Status | DONE |
| Depends On | — |
| Blocks | T002, T003, T004, T005 |

## Description

Create the `src/vault/` module with `VaultManager` class and `VaultException`. This is a prerequisite for all other tasks since the GUI code imports from `vault.manager`. The implementation must match the interface expected by existing tests in `tests/test_vault_manager.py`.

## Acceptance Criteria

- [ ] `src/vault/__init__.py` exists
- [ ] `src/vault/manager.py` implements `VaultManager` class with SQLite backend
- [ ] `VaultException` is defined and raised appropriately
- [ ] Methods: `add_recording()`, `get_recordings()`, `update_recording()`, `delete_recording()`
- [ ] JSON field handling for `key_points` and `tags`
- [ ] Database migration support (remove `archived` column)
- [ ] All existing tests in `tests/test_vault_manager.py` pass
