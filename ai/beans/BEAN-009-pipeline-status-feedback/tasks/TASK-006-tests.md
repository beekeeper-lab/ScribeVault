# TASK-006: Write Tests for Pipeline Status

## Metadata

| Field     | Value        |
|-----------|--------------|
| Task      | TASK-006     |
| Title     | Write Tests for Pipeline Status |
| Owner     | tech-qa      |
| Priority  | 6            |
| Status    | DONE         |
| Depends   | TASK-001, TASK-002, TASK-005 |
| Started   | —            |
| Completed | —            |
| Duration  | —            |
| Tokens    | —            |

## Description

Write comprehensive tests covering the pipeline status model, worker stage signals, and vault persistence. Tests should cover happy paths, failure scenarios, and edge cases (e.g., retry after failure, skipped stages, serialization round-trips).

## Acceptance Criteria

- [ ] Tests for PipelineStatus model: creation, state transitions, serialization/deserialization
- [ ] Tests for RecordingWorker stage signals: verify correct signals emitted for success, failure, and skip scenarios
- [ ] Tests for vault persistence: pipeline status stored and retrieved correctly
- [ ] Tests for retry logic: verify only the failed stage is re-executed
- [ ] All new tests pass (`pytest tests/`)
- [ ] No existing tests broken by changes
