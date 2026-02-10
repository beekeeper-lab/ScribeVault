# TASK-002: Integrate Logging Config into Entry Points

## Metadata

| Field     | Value        |
|-----------|--------------|
| Task      | TASK-002     |
| Bean      | BEAN-008     |
| Owner     | developer    |
| Priority  | 2            |
| Status    | TODO         |
| Depends   | TASK-001     |
| Started   | —            |
| Completed | —            |
| Duration  | —            |
| Tokens    | —            |

## Description

Update `main.py` and `main_qt.py` to call `setup_logging()` at startup before any other imports that use logging. Replace `print()` calls in entry point exception handlers with logger calls.

## Acceptance Criteria

- [ ] `main.py` calls `setup_logging()` before creating the application
- [ ] `main_qt.py` calls `setup_logging()` before creating the Qt application
- [ ] `print()` calls in entry point exception handlers replaced with `logger.error()`
- [ ] Both entry points import from `config.logging_config`
