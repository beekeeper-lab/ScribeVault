# TASK-001: Create Centralized Logging Configuration Module

## Metadata

| Field     | Value        |
|-----------|--------------|
| Task      | TASK-001     |
| Bean      | BEAN-008     |
| Owner     | developer    |
| Priority  | 1            |
| Status    | TODO         |
| Depends   | none         |
| Started   | —            |
| Completed | —            |
| Duration  | —            |
| Tokens    | —            |

## Description

Create `src/config/logging_config.py` with a centralized logging setup function that configures:
- Root logger with a consistent formatter (timestamp, level, module, message)
- Console handler (StreamHandler to stderr)
- File handler writing to a log file (e.g., `scribevault.log` in the app directory)
- Configurable log level (DEBUG/INFO/WARNING) passed as parameter
- Thread-safe configuration (Python logging is thread-safe by default)

The function should be called once from entry points and should NOT use `logging.basicConfig()`.

## Acceptance Criteria

- [ ] File `src/config/logging_config.py` exists with a `setup_logging(level, log_file)` function
- [ ] Function configures root logger with both console and file handlers
- [ ] Log format includes: timestamp, log level, logger name, message
- [ ] Function is idempotent (safe to call multiple times without duplicating handlers)
- [ ] Default log level is INFO, default log file is `scribevault.log`
