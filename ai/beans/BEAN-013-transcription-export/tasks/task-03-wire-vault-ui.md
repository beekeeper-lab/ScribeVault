# Task 03: Wire Export to Vault UI

| Field      | Value          |
|------------|----------------|
| Owner      | developer      |
| Status     | TODO           |
| Depends On | task-02        |

## Description

Replace the stubbed `export_recording()` method in `src/gui/qt_vault_dialog.py` with a working implementation that:
- Shows a format selection dialog (TXT, Markdown, SRT)
- Uses `QFileDialog` to let user choose save location
- Calls `TranscriptionExporter` to generate the export
- Shows size warning if transcription >50KB
- Shows success/error feedback via status bar and message boxes

## Acceptance Criteria

- [ ] Export button triggers format selection
- [ ] File save dialog with appropriate file extension filter
- [ ] Size warning for large transcriptions
- [ ] Success/error feedback to user
