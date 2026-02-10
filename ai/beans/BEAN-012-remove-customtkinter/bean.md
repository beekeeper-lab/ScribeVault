# BEAN-012: Remove CustomTkinter Implementation

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-012     |
| Title     | Remove CustomTkinter Implementation |
| Type      | enhancement |
| Priority  | P2 |
| Status    | Approved   |
| Created   | 2026-02-10   |
| Started   |              |
| Completed |              |
| Duration  |              |

## Problem Statement

The codebase maintains two complete GUI implementations: CustomTkinter (`src/gui/main_window.py`, 1646 lines) and PySide6 (`src/gui/qt_main_window.py`, 897 lines). This causes:
1. Bug fixes must be applied to both implementations
2. Testing burden is doubled
3. Dependency bloat (both customtkinter and PySide6 in requirements)
4. Confusion about which entry point to use (`main.py` vs `main_qt.py`)
5. ~700 lines of duplicated logic

## Goal

Remove the CustomTkinter implementation entirely, making PySide6 the single GUI framework. Consolidate to a single entry point.

## Scope

### In Scope

- Remove `src/gui/main_window.py` (CustomTkinter main window)
- Remove `src/gui/settings_window.py` (CustomTkinter settings)
- Remove `main.py` entry point (keep `main_qt.py` only, rename to `main.py`)
- Remove `customtkinter` from requirements.txt
- Remove any CustomTkinter-specific assets or imports
- Update README and documentation to reflect single GUI
- Update all references to `main.py` / `main_qt.py`

### Out of Scope

- Rewriting PySide6 components
- Adding new features
- Changing the PySide6 UI design

## Acceptance Criteria

- [ ] `src/gui/main_window.py` (CustomTkinter) removed
- [ ] `src/gui/settings_window.py` (CustomTkinter) removed
- [ ] Single entry point: `main.py` launches PySide6
- [ ] `customtkinter` removed from requirements.txt
- [ ] No remaining imports of customtkinter anywhere in codebase
- [ ] README updated to reflect PySide6 as the only GUI
- [ ] All existing PySide6 tests still pass

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

DEPENDS ON: BEAN-010 (PySide6 Feature Parity) -- must be completed first to ensure no features are lost. Touches `src/gui/`, `main.py`, `main_qt.py`, `requirements.txt`, `README.md`.
