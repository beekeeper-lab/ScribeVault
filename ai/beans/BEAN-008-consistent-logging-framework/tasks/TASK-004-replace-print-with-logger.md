# TASK-004: Replace print() Warning/Error Calls with Logger

## Metadata

| Field     | Value        |
|-----------|--------------|
| Task      | TASK-004     |
| Bean      | BEAN-008     |
| Owner     | developer    |
| Priority  | 4            |
| Status    | TODO         |
| Depends   | TASK-001     |
| Started   | —            |
| Completed | —            |
| Duration  | —            |
| Tokens    | —            |

## Description

Replace all `print()` calls used for warnings, errors, and debug messages with proper `logger` calls. Add `import logging` and `logger = logging.getLogger(__name__)` to modules that don't already have it.

Files to update:
- `src/ai/summarizer.py` — 7 print statements (warnings/errors)
- `src/audio/recorder.py` — 2 print statements (errors)
- `src/gui/settings_window.py` — 5 print statements (errors)
- `src/gui/main_window.py` — 23 print statements (DEBUG + errors)
- `src/config/settings.py` — 2 print statements (errors)
- `src/transcription/whisper_service.py` — 6 print statements (warnings/errors)

Mapping:
- `print(f"Warning: ...")` → `logger.warning(...)`
- `print(f"Error: ...")` → `logger.error(...)`
- `print(f"DEBUG: ...")` → `logger.debug(...)`
- `print("⚠️ ...")` → `logger.warning(...)`

## Acceptance Criteria

- [ ] No `print()` calls for warnings/errors/debug remain in `src/` modules
- [ ] All replacement calls use appropriate log levels (debug/info/warning/error)
- [ ] Modules that didn't have logger setup now have `logger = logging.getLogger(__name__)`
- [ ] Log messages are clean (no emoji prefixes like ⚠️ in log calls)
