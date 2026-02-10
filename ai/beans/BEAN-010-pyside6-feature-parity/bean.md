# BEAN-010: PySide6 Feature Parity with CustomTkinter

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-010     |
| Title     | PySide6 Feature Parity with CustomTkinter |
| Type      | enhancement |
| Priority  | P2 |
| Status    | Unapproved   |
| Created   | 2026-02-10   |
| Started   |              |
| Completed |              |
| Duration  |              |

## Problem Statement

The PySide6 version (`main_qt.py`) is missing several features that exist in the CustomTkinter version (`main.py`):
1. Settings persistence uses QSettings which may not align with `config/settings.json` -- settings changed in PySide6 may not persist correctly.
2. Audio playback in vault is not fully implemented.
3. Recording details view (full metadata, timestamps, file paths) is incomplete.
4. Theme/appearance settings don't fully work in PySide6.

## Goal

PySide6 version has full feature parity with CustomTkinter version, making it safe to eventually remove the old implementation.

## Scope

### In Scope

- Fix settings persistence: ensure PySide6 settings read/write through the same `settings.json` as the CustomTkinter version
- Implement audio playback from vault (play button that opens/plays the audio file)
- Complete recording details view (show all metadata, timestamps, file sizes)
- Ensure theme/appearance settings work correctly
- Test all features work end-to-end

### Out of Scope

- New features not in CustomTkinter version
- Removing CustomTkinter (separate bean)
- Redesigning the UI layout

## Acceptance Criteria

- [ ] Settings saved in PySide6 are read correctly on next launch
- [ ] Settings match between PySide6 and CustomTkinter when using same config file
- [ ] Audio playback works from vault (play button launches audio)
- [ ] Recording details view shows full metadata (title, date, duration, file size, category)
- [ ] Theme settings apply correctly in PySide6
- [ ] All features in CustomTkinter main window have PySide6 equivalents

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 |      |       |            | TODO   |
| 2 |      |       |            | TODO   |
| 3 |      |       |            | TODO   |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

No dependencies on other beans. Prerequisite for BEAN-012 (Remove CustomTkinter). Touches `src/gui/qt_main_window.py`, `src/gui/qt_settings_dialog.py`, `src/gui/qt_vault_dialog.py`.
