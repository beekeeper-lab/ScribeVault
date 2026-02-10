# Task 005: Implement Edit Recording in PySide6 Vault

| Field | Value |
|-------|-------|
| Task ID | BEAN-010-T005 |
| Owner | developer |
| Status | TODO |
| Depends On | T001, T004 |
| Priority | P1 |

## Description

Implement recording editing functionality in the PySide6 vault dialog. Port from CustomTkinter's `_edit_recording()` method (main_window.py:1200+). Allow editing title, description, and category with save/cancel, then refresh the vault.

## Acceptance Criteria

- [ ] Edit dialog opens with pre-populated fields (title, description, category)
- [ ] Save persists changes via `VaultManager.update_recording()`
- [ ] Cancel closes dialog without changes
- [ ] Vault table refreshes after save
