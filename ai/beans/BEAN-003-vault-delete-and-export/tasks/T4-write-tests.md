# T4: Write Tests for Delete and Export Functionality

## Owner: tech-qa

## Depends On: T2, T3

## Status: DONE

## Description

Add test coverage for the new delete and export functionality. Create `tests/test_vault_delete_export.py` with tests covering:
1. Delete recording removes DB entry and files
2. Delete with confirmation (mock dialog)
3. Export copies files correctly
4. Error handling for missing files, permissions
5. Vault list refresh after operations

## Acceptance Criteria

- [ ] Tests for VaultManager.delete_recording() with file cleanup
- [ ] Tests for export logic (file copying, .txt/.md generation)
- [ ] Tests for error handling paths
- [ ] All tests pass with pytest

## Files to Create/Modify

- Create: `tests/test_vault_delete_export.py`
