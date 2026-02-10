# BEAN-008: Consistent Logging Framework

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-008     |
| Title     | Consistent Logging Framework |
| Type      | enhancement |
| Priority  | P2 |
| Status    | Unapproved   |
| Created   | 2026-02-10   |
| Started   |              |
| Completed |              |
| Duration  |              |

## Problem Statement

Error reporting is inconsistent across the codebase:
- `src/transcription/whisper_service.py` uses `print()` for warnings (e.g., "OpenAI API key not configured")
- `src/config/settings.py` uses `logger.warning()`
- `src/gui/` modules use `QMessageBox` for some errors and silently swallow others
- Multiple modules call `logging.basicConfig()` independently (only the first call takes effect)
- No centralized logging configuration

## Goal

All modules use a consistent logging framework with a single configuration point, proper log levels, and structured output.

## Scope

### In Scope

- Create centralized logging configuration (called once in main entry points)
- Replace all `print()` warning/error calls with proper `logger.warning()`/`logger.error()`
- Remove duplicate `logging.basicConfig()` calls from individual modules
- Add file-based log output in addition to console
- Ensure GUI error dialogs are backed by log entries

### Out of Scope

- Log aggregation or remote logging
- Structured JSON logging
- Log rotation (keep it simple with single file)

## Acceptance Criteria

- [ ] Single `logging` configuration in main entry points (`main.py`, `main_qt.py`)
- [ ] All `print()` calls for warnings/errors replaced with `logger.warning()`/`logger.error()`
- [ ] No duplicate `logging.basicConfig()` calls in individual modules
- [ ] Logs written to both console and a log file
- [ ] Log level configurable (DEBUG/INFO/WARNING in settings)
- [ ] Existing tests still pass

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

No dependencies on other beans. Touches all source files but changes are mechanical (print to logger). Low merge conflict risk since changes are on different lines than other beans.
