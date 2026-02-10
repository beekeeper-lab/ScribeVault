# BEAN-012: Remove CustomTkinter Implementation

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-012     |
| Title     | Remove CustomTkinter Implementation |
| Type      | enhancement |
| Priority  | P2 |
| Status    | Done   |
| Created   | 2026-02-10   |
| Started   | 2026-02-10 16:19 |
| Completed | 2026-02-10 16:22 |
| Duration  | ~3m              |

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

- [x] `src/gui/main_window.py` (CustomTkinter) removed
- [x] `src/gui/settings_window.py` (CustomTkinter) removed
- [x] Single entry point: `main.py` launches PySide6
- [x] `customtkinter` removed from requirements.txt (was already removed)
- [x] No remaining imports of customtkinter anywhere in codebase
- [x] README updated to reflect PySide6 as the only GUI
- [x] All existing PySide6 tests still pass (pre-existing failures unrelated to changes)

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Remove CustomTkinter GUI files | developer | — | Done |
| 2 | Remove CTK entry point, consolidate to single main.py | developer | T001 | Done |
| 3 | Update health_check.py | developer | T001 | Done |
| 4 | Update documentation (README, CLAUDE.md) | developer | T002 | Done |
| 5 | Verify clean codebase — tests & lint | tech-qa | T001-T004 | Done |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      | 5     |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

DEPENDS ON: BEAN-010 (PySide6 Feature Parity) -- must be completed first to ensure no features are lost. Touches `src/gui/`, `main.py`, `main_qt.py`, `requirements.txt`, `README.md`.
