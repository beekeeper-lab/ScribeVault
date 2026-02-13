# BEAN-034: Dead Code & Unused Import Cleanup

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-034     |
| Title     | Dead Code & Unused Import Cleanup |
| Type      | enhancement |
| Priority  | P1 |
| Status    | Unapproved   |
| Created   | 2026-02-13   |
| Started   |              |
| Completed |              |
| Duration  |              |

## Problem Statement

The codebase has accumulated significant dead code and unused imports across multiple files. `qt_main_window.py` has 20 unused imports, `qt_app.py` has 8, and several source files contain dead methods that are never called. This increases cognitive load, slows IDE navigation, and makes the codebase harder to maintain. A flake8 scan reports 34 F401 (unused import) violations across `src/`.

## Goal

All dead code and unused imports are removed. `flake8 src/ --select=F401` reports zero violations.

## Scope

### In Scope

- Remove 20 unused imports from `src/gui/qt_main_window.py` (sys, os, traceback, QGridLayout, QScrollArea, QTabWidget, QMenuBar, QToolBar, QSystemTrayIcon, QThread, QSize, QRect, QPixmap, QPalette, QColor, QPainter, QBrush, AudioException, TranscriptionException, VaultException)
- Remove 8 unused imports from `src/gui/qt_app.py` (sys, QTimer, QPalette, SettingsManager, AudioRecorder, WhisperService, SummarizerService, VaultManager)
- Remove unused imports from `src/gui/qt_settings_dialog.py` (os, Optional, QProgressBar, QFont, QIcon)
- Remove unused import `os` from `src/export/markdown_generator.py`
- Remove dead method `_create_dummy_recording` from `src/audio/recorder.py` (lines 593-637)
- Remove dead method `_record_loop` from `src/audio/recorder.py` (lines 285-299)
- Remove dead method `get_service_comparison` from `src/config/settings.py` (lines 775-823)
- Remove dead function `check_local_whisper_availability` from `src/transcription/whisper_service.py` (lines 389-423)
- Fix bare `except:` in `src/export/markdown_generator.py` line 73 to `except (ValueError, TypeError):`
- Fix unused variable `e` in `src/gui/qt_main_window.py` line 108

### Out of Scope

- Refactoring code structure or class decomposition (God class issues)
- Fixing lint warnings other than F401, E722, F841
- Removing whitespace-only lint issues (W293) — those can be fixed with `black`

## Acceptance Criteria

- [ ] `flake8 src/ --select=F401` reports 0 violations
- [ ] `flake8 src/ --select=E722` reports 0 violations (bare except fixed)
- [ ] `flake8 src/ --select=F841` reports 0 violations (unused variable fixed)
- [ ] Dead methods `_create_dummy_recording`, `_record_loop`, `get_service_comparison`, `check_local_whisper_availability` are removed
- [ ] All existing tests still pass
- [ ] No runtime import errors introduced by removing imports

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Remove unused imports from all src/ files | developer | | TODO |
| 2 | Remove dead methods from recorder.py, settings.py, whisper_service.py | developer | | TODO |
| 3 | Fix bare except in markdown_generator.py | developer | | TODO |
| 4 | Fix unused variable in qt_main_window.py | developer | | TODO |
| 5 | Run full test suite to verify no regressions | tech-qa | 1-4 | TODO |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

Depends on BEAN-031 (Fix Broken Test Suite) for the verification step — some tests need to pass before we can confirm no regressions. However, the cleanup work itself can proceed independently.

Full flake8 scan found 464 violations total, but 395 are W293 (whitespace on blank lines) which are cosmetic and auto-fixable with `black`. This bean focuses on the semantically meaningful issues (unused imports, dead code, bare except).
