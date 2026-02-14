# BEAN-038: Stale Documentation & UI Fixes

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-038     |
| Title     | Stale Documentation & UI Fixes |
| Type      | enhancement |
| Priority  | P3 |
| Status    | In Progress  |
| Created   | 2026-02-13   |
| Started   |              |
| Completed |              |
| Duration  |              |

## Problem Statement

A comprehensive markdown audit found extensive stale documentation and several UI bugs:

**Obsolete Files (should be deleted):**
- `PYSIDE6_MIGRATION.md` — completed migration plan, references non-existent files
- `PYSIDE6_README.md` — references removed files (`setup_pyside6.py`, `runApp_qt.sh`, `main_qt.py`), duplicates README.md
- `FEATURE_SUMMARY.md` — stale feature implementation log from `feature/local-whisper-option` branch, references removed files (`src/gui/settings_window.py`, `src/gui/main_window.py`)

**Outdated Files (need updating):**
- `SECURITY.md` — recommends `.env` approach replaced by keyring in BEAN-004; missing BEAN-026 through BEAN-030 security features
- `CONTRIBUTING.md` — references `.env.example` to `.env` setup, removed in BEAN-004
- `docs/CONFIGURATION.md` — references `src/gui/settings_window.py` (removed), shows `gpt-3.5-turbo` as default
- `.github/copilot-instructions.md` — states "GUI Framework: CustomTkinter" (should be PySide6)
- `CLAUDE.md` — references `ai/context/bean-workflow.md` and `ai/context/decisions.md` which don't exist

**Bean Status Inconsistencies:**
- BEAN-021: Index says Done, bean says Approved with all tasks TODO
- BEAN-003, BEAN-007, BEAN-015, BEAN-016, BEAN-025, BEAN-026, BEAN-027: Index says Done but acceptance criteria are unchecked

**UI Issues:**
- `Ctrl+S` mapped to "Copy Summary" (conflicts with universal "Save")
- `Ctrl+V` mapped to "View Vault" (conflicts with universal "Paste")
- `Space` toggles recording but fires when typing in text fields
- `AnimatedRecordButton` opacity animation broken (QPushButton has no opacity property)
- `play_audio` uses wrong directory path (`recordings/` vs `vault_dir`)
- SRT export writes to wrong subdirectory

## Goal

Documentation accurately reflects the current codebase. Bean statuses are internally consistent. UI keyboard shortcuts follow platform conventions. Broken animation and file paths are fixed.

## Scope

### In Scope

- Delete obsolete files: `PYSIDE6_MIGRATION.md`, `PYSIDE6_README.md`, `FEATURE_SUMMARY.md`
- Update `SECURITY.md` to reflect keyring/encrypted storage and BEAN-026 through BEAN-030
- Update `CONTRIBUTING.md` to fix API key setup instructions
- Update `docs/CONFIGURATION.md` to fix file references and model names
- Update `.github/copilot-instructions.md` to reference PySide6
- Fix `CLAUDE.md` references to non-existent `ai/context/` files
- Fix bean status inconsistencies (check acceptance criteria, fix BEAN-021 status)
- Fix keyboard shortcuts: remap `Ctrl+S`, `Ctrl+V`, and `Space` to non-conflicting bindings
- Fix `AnimatedRecordButton` opacity animation to use `QGraphicsOpacityEffect`
- Fix `play_audio` to use correct vault directory path
- Fix SRT export to write to the per-recording subfolder
- Add `validate_path_within()` check to `open_markdown_file()` in `qt_summary_viewer.py` before passing path to system opener (security gap found in audit -- `play_audio` validates but `open_markdown_file` does not)

### Out of Scope

- Updating completed bean status reports (historical records)
- Removing `ai-team-library/` references from agent files (shared template concern)
- Refactoring the main window or vault dialog classes
- Creating missing `ai/context/` files (separate concern)

## Acceptance Criteria

- [ ] `PYSIDE6_MIGRATION.md`, `PYSIDE6_README.md`, `FEATURE_SUMMARY.md` are deleted
- [ ] `SECURITY.md` reflects current security architecture (keyring, encryption, path validation, HTML escaping, permissions)
- [ ] `CONTRIBUTING.md` no longer references `.env` for API key setup
- [ ] `docs/CONFIGURATION.md` references correct files and models
- [ ] `.github/copilot-instructions.md` references PySide6 (not CustomTkinter)
- [ ] All Done beans have checked acceptance criteria and consistent status
- [ ] No keyboard shortcut conflicts with OS conventions (Ctrl+S, Ctrl+V, Space)
- [ ] Record button animation works (opacity effect applied correctly)
- [ ] `play_audio` opens the correct audio file from the vault directory
- [ ] SRT export goes to the same subfolder as other export files
- [ ] `open_markdown_file()` validates path with `validate_path_within()` before invoking system opener
- [ ] All existing tests pass

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Delete 3 obsolete markdown files | developer | | TODO |
| 2 | Update SECURITY.md with current security features | developer | | TODO |
| 3 | Update CONTRIBUTING.md, docs/CONFIGURATION.md | developer | | TODO |
| 4 | Update .github/copilot-instructions.md | developer | | TODO |
| 5 | Fix CLAUDE.md ai/context references | developer | | TODO |
| 6 | Fix bean status inconsistencies (8 beans) | developer | | TODO |
| 7 | Fix keyboard shortcut conflicts | developer | | TODO |
| 8 | Fix AnimatedRecordButton opacity animation | developer | | TODO |
| 9 | Fix play_audio directory path | developer | | TODO |
| 10 | Fix SRT export path | developer | | TODO |
| 11 | Add path validation to open_markdown_file() | developer | | TODO |
| 12 | Verify all fixes and run tests | tech-qa | 1-11 | TODO |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

The `play_audio` bug (task 9) means audio playback from the vault dialog is currently broken on all platforms — it looks for files in `recordings/` instead of the vault directory. This is arguably a P2 bug on its own but is grouped here for efficiency.

Suggested keyboard shortcut replacements:
- `Ctrl+S` (Copy Summary) → `Ctrl+Shift+C` or `Ctrl+Y`
- `Ctrl+V` (View Vault) → `Ctrl+Shift+V` or `Ctrl+B`
- `Space` (Toggle Recording) → Remove shortcut or use `Ctrl+R`

Bean status inconsistencies found:
- BEAN-021: Index=Done, Bean=Approved, all tasks TODO — needs investigation
- BEAN-003, BEAN-007, BEAN-015, BEAN-016, BEAN-025: Criteria unchecked but tasks Done
- BEAN-026, BEAN-027: All criteria unchecked AND all tasks still marked TODO despite Done in index

README.md updates removed from this bean's scope during backlog consolidation — handled by BEAN-043 (Comprehensive README Rewrite).

This is a large bean with 11 tasks. Consider splitting documentation fixes from UI fixes if the scope feels too broad.
