# T2: Implement delete_recording in Vault Dialog

## Owner: developer

## Depends On: T1

## Status: DONE

## Description

Replace the stub `delete_recording()` method in `src/gui/qt_vault_dialog.py` with a real implementation that:
1. Shows confirmation dialog (already partially implemented)
2. Calls `VaultManager.delete_recording(recording_id)` to remove the DB entry
3. Deletes associated files (audio file, transcription, summary/markdown)
4. Refreshes the vault list after deletion
5. Shows error dialog on failure

## Acceptance Criteria

- [ ] Delete button shows confirmation dialog before deleting
- [ ] Delete removes audio file, transcription, summary, and database entry
- [ ] Vault list refreshes after deletion
- [ ] Error dialog shown if delete fails (e.g., file locked, permission denied)

## Files to Modify

- `src/gui/qt_vault_dialog.py` — `delete_recording()` method
