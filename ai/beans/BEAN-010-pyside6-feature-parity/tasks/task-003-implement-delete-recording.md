# Task 003: Implement Delete Recording in PySide6 Vault Dialog

| Field | Value |
|-------|-------|
| Task ID | BEAN-010-T003 |
| Owner | developer |
| Status | TODO |
| Depends On | T001 |
| Priority | P0 |

## Description

Replace the "coming soon" stub in `qt_vault_dialog.py:457-459` with actual delete functionality that calls `VaultManager.delete_recording()`. Port the behavior from CustomTkinter `main_window.py:523-690` — confirmation dialog, database deletion, optional audio file deletion, and vault refresh.

## Acceptance Criteria

- [ ] Delete button triggers confirmation dialog
- [ ] Confirmed deletion removes recording from vault database
- [ ] Optionally deletes the audio file on disk
- [ ] Recordings table refreshes after deletion
- [ ] Status bar shows deletion result
