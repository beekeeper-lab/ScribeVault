# TASK-003: Remove Duplicate logging.basicConfig() Calls

## Metadata

| Field     | Value        |
|-----------|--------------|
| Task      | TASK-003     |
| Bean      | BEAN-008     |
| Owner     | developer    |
| Priority  | 3            |
| Status    | TODO         |
| Depends   | TASK-001     |
| Started   | —            |
| Completed | —            |
| Duration  | —            |
| Tokens    | —            |

## Description

Remove all `logging.basicConfig()` calls from individual modules. These modules should only use `logging.getLogger(__name__)` — the root logger configuration is handled centrally by the entry points.

Files to update:
- `src/audio/recorder.py` (line 17)
- `src/gui/qt_main_window.py` (line 39)
- `src/gui/main_window.py` (line 27)
- `src/config/settings.py` (line 14)
- `src/transcription/whisper_service.py` (line 14)

## Acceptance Criteria

- [ ] No `logging.basicConfig()` calls remain in any module under `src/`
- [ ] Each module retains its `logger = logging.getLogger(__name__)` line
- [ ] No module-level logging configuration remains outside entry points
