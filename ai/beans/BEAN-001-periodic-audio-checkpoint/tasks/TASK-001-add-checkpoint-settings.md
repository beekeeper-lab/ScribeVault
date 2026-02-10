# TASK-001: Add Checkpoint Interval to AppSettings

## Metadata

| Field     | Value          |
|-----------|----------------|
| Task      | TASK-001       |
| Bean      | BEAN-001       |
| Owner     | developer      |
| Priority  | 1              |
| Status    | TODO           |
| Depends   | none           |
| Started   | —              |
| Completed | —              |
| Duration  | —              |
| Tokens    | —              |

## Description

Add a `checkpoint_interval_seconds` configuration field to the application settings so users can control how often audio frames are flushed to disk during recording. The default value should be 30 seconds.

## Acceptance Criteria

- [ ] `AppSettings` dataclass includes a `checkpoint_interval_seconds: int` field with default value `30`
- [ ] Validation ensures interval is between 10 and 300 seconds
- [ ] Setting is serialized/deserialized correctly in `settings.json`
- [ ] Existing settings tests still pass
