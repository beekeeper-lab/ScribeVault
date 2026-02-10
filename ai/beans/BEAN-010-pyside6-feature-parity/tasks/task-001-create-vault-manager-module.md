# Task 001: Create Vault Manager Module

| Field | Value |
|-------|-------|
| Task ID | BEAN-010-T001 |
| Owner | developer |
| Status | TODO |
| Depends On | — |
| Priority | P0 |

## Description

The `vault.manager` module is imported by all GUI code but doesn't exist in the source tree. Create a `src/vault/` package with `__init__.py` and `manager.py` implementing `VaultManager` and `VaultException` as expected by the existing tests in `tests/test_vault_manager.py`.

## Acceptance Criteria

- [ ] `src/vault/__init__.py` exists
- [ ] `src/vault/manager.py` implements `VaultManager` class with: `add_recording()`, `get_recordings()`, `update_recording()`, `delete_recording()`, `_init_database()`, `vault_dir`, `db_path`
- [ ] `VaultException` is defined
- [ ] All tests in `tests/test_vault_manager.py` pass
