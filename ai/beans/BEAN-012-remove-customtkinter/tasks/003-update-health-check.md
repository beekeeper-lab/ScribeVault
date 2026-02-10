# Task 003: Update Health Check Script

## Metadata

| Field | Value |
|-------|-------|
| Task ID | BEAN-012-T003 |
| Owner | developer |
| Status | Done |
| Depends On | T001 |

## Description

Update `health_check.py` to remove CustomTkinter references:

1. Remove `("customtkinter", "customtkinter")` from the `required` list in `check_dependencies()`
2. Replace `"gui.main_window"` with `"gui.qt_main_window"` in the `critical_imports` list in `check_imports()`
3. Add PySide6 to the dependency check list

## Acceptance Criteria

- [ ] No customtkinter references remain in health_check.py
- [ ] PySide6 is checked as a dependency
- [ ] Critical imports reference PySide6 modules instead of CustomTkinter
