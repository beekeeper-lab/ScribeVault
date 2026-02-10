# Task 003: Add Audio Settings Tab to Settings Dialog

## Owner
developer

## Depends On
task-001, task-002

## Status
TODO

## Description
Add an "Audio" tab to `src/gui/qt_settings_dialog.py` with quality preset selection, input device dropdown, and file size estimation display.

### UI Elements
- Quality preset dropdown (Voice / Standard / High Quality)
- Preset description label showing parameters
- Input device dropdown populated from `get_audio_devices()`
- Refresh devices button
- Estimated file size per minute display (updates on preset change)

### Acceptance Criteria
- Audio tab visible in settings dialog
- Preset selection updates description and file size estimate
- Device dropdown shows available input devices
- Settings are saved/loaded correctly
- File size estimate shown per preset
