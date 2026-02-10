# Task 002: Remove CustomTkinter Entry Point and Consolidate to Single Entry

## Metadata

| Field | Value |
|-------|-------|
| Task ID | BEAN-012-T002 |
| Owner | developer |
| Status | Done |
| Depends On | T001 |

## Description

Remove the old `main.py` entry point (CustomTkinter launcher) and rename `main_qt.py` to `main.py` to establish a single entry point.

## Steps

1. Delete `main.py` (CustomTkinter entry point, 36 lines)
2. Rename `main_qt.py` → `main.py` (PySide6 entry point)
3. Update any internal references in the renamed file if needed

## Acceptance Criteria

- [ ] Old `main.py` (CustomTkinter) is removed
- [ ] `main_qt.py` is renamed to `main.py`
- [ ] `python main.py` launches the PySide6 GUI
- [ ] No `main_qt.py` file remains
