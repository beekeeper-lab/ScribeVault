# BEAN-036: Extract Shared Utility Functions

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-036     |
| Title     | Extract Shared Utility Functions |
| Type      | enhancement |
| Priority  | P2 |
| Status    | Unapproved   |
| Created   | 2026-02-13   |
| Started   |              |
| Completed |              |
| Duration  |              |

## Problem Statement

Several utility functions are duplicated across multiple files, creating maintenance burden and inconsistent behavior:

1. **`format_duration`** — implemented 4 times with slightly different formats:
   - `src/gui/qt_vault_dialog.py` (lines 1512-1530)
   - `src/gui/qt_summary_viewer.py` (lines 1138-1156)
   - `src/export/transcription_exporter.py` (lines 52-63)
   - `src/export/markdown_generator.py` (lines 155-169)

2. **`format_file_size`** — duplicated identically in 2 places:
   - `src/gui/qt_vault_dialog.py`
   - `src/gui/qt_summary_viewer.py`

3. **Date parsing** (`datetime.fromisoformat` with `Z` replacement) — duplicated 3 times:
   - `src/export/markdown_generator.py` (lines 68-74)
   - `src/export/transcription_exporter.py` (lines 65-76)
   - `src/gui/qt_vault_dialog.py` (lines 416-428)

4. **Platform-aware file opener** (`os.startfile` / `subprocess "open"` / `xdg-open`) — duplicated 3 times:
   - `src/gui/qt_vault_dialog.py` (lines 1326-1364, 1366-1416)
   - `src/gui/qt_summary_viewer.py` (lines 1098-1136)

5. **Version string** `"2.0.0"` / `"v2.0.0"` — hardcoded in 3 places:
   - `src/gui/qt_main_window.py` (lines 567, 1199)
   - `src/gui/qt_app.py` (line 31)

6. **Font name** `"Segoe UI"` — hardcoded across multiple GUI files (Windows-only font)

## Goal

Create a shared utility module and a version constant to eliminate all duplicated code. Each utility function exists in exactly one place.

## Scope

### In Scope

- Create `src/utils.py` (or `src/common/formatting.py`) with shared functions: `format_duration()`, `format_file_size()`, `parse_datetime()`, `open_with_system_app()`
- Create a `__version__` constant in `src/__init__.py` or a dedicated `src/version.py`
- Define a `FONT_FAMILY` constant (with cross-platform fallback stack)
- Update all call sites to use the shared functions
- Remove the duplicated implementations
- Add tests for the shared utility functions

### Out of Scope

- Refactoring God classes (ScribeVaultMainWindow, VaultDialog)
- Changing the formatting behavior — keep existing output format
- Standardizing all format_duration implementations to one style (pick the most common one)

## Acceptance Criteria

- [ ] `format_duration` exists in exactly 1 location, called from all 4 original sites
- [ ] `format_file_size` exists in exactly 1 location, called from both original sites
- [ ] `parse_datetime` exists in exactly 1 location, called from all 3 original sites
- [ ] `open_with_system_app` exists in exactly 1 location, called from all 3 original sites
- [ ] Version string defined in 1 constant, referenced everywhere
- [ ] Font family defined in 1 constant with cross-platform fallback
- [ ] Tests exist for all shared utility functions
- [ ] All existing tests pass

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Create src/utils.py with shared formatting functions | developer | | TODO |
| 2 | Create version constant | developer | | TODO |
| 3 | Create font family constant | developer | | TODO |
| 4 | Update all call sites to use shared functions | developer | 1-3 | TODO |
| 5 | Write tests for shared utilities | tech-qa | 1 | TODO |
| 6 | Verify no regressions | tech-qa | 4-5 | TODO |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

The 4 implementations of `format_duration` produce slightly different output formats (some use `Xh Xm Xs`, others use `X:XX`). The consolidation should pick the most common format or the one used in the most user-visible context, and update all call sites consistently.
