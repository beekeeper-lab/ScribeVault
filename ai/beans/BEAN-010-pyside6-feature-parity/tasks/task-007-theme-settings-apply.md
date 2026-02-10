# Task 007: Theme Settings Apply Correctly in PySide6

| Field | Value |
|-------|-------|
| Task ID | BEAN-010-T007 |
| Owner | developer |
| Status | TODO |
| Depends On | — |
| Priority | P1 |

## Description

Ensure theme/appearance settings work correctly in PySide6. Currently `qt_settings_dialog.py` lets users choose dark/light/system themes, but after saving, the main window should apply the theme. Port the `on_settings_changed()` callback pattern from CustomTkinter (main_window.py:1320-1330).

## Acceptance Criteria

- [ ] Theme changes in settings dialog apply to main window after save
- [ ] Dark, light, and system themes are visually distinct
- [ ] Theme persists across application restarts via settings.json
