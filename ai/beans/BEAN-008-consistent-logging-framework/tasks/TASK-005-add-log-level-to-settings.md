# TASK-005: Add Log Level Configuration to Settings

## Metadata

| Field     | Value        |
|-----------|--------------|
| Task      | TASK-005     |
| Bean      | BEAN-008     |
| Owner     | developer    |
| Priority  | 5            |
| Status    | TODO         |
| Depends   | TASK-001     |
| Started   | —            |
| Completed | —            |
| Duration  | —            |
| Tokens    | —            |

## Description

Add a `log_level` field to the application settings so users can configure verbosity. The entry points should read this setting and pass it to `setup_logging()`.

Changes:
- Add `log_level: str = "INFO"` to `AppSettings` dataclass in `src/config/settings.py`
- Entry points read the setting and pass to `setup_logging()`
- Valid values: DEBUG, INFO, WARNING

## Acceptance Criteria

- [ ] `AppSettings` has a `log_level` field with default "INFO"
- [ ] Entry points pass the configured log level to `setup_logging()`
- [ ] Log level persists across application restarts (saved in config JSON)
