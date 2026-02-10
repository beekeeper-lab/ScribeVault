# T3: Implement export_recording in Vault Dialog

## Owner: developer

## Depends On: T1

## Status: DONE

## Description

Replace the stub `export_recording()` method in `src/gui/qt_vault_dialog.py` with a real implementation that:
1. Opens a directory picker dialog (QFileDialog.getExistingDirectory)
2. Copies the audio file to the chosen directory
3. Writes transcription as a .txt file
4. Writes summary as a .md file
5. Shows success/error dialog

## Acceptance Criteria

- [ ] Export opens a directory picker dialog
- [ ] Export copies audio file to chosen directory
- [ ] Export writes transcription (.txt) to chosen directory
- [ ] Export writes summary (.md) to chosen directory
- [ ] Error dialog shown if export fails (e.g., permission denied)

## Files to Modify

- `src/gui/qt_vault_dialog.py` — `export_recording()` method
