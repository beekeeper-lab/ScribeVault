# TASK-001: Create PipelineStatus Data Model

## Metadata

| Field     | Value        |
|-----------|--------------|
| Task      | TASK-001     |
| Title     | Create PipelineStatus Data Model |
| Owner     | developer    |
| Priority  | 1            |
| Status    | DONE         |
| Depends   | none         |
| Started   | —            |
| Completed | —            |
| Duration  | —            |
| Tokens    | —            |

## Description

Create a `PipelineStatus` data model class that tracks the status of each pipeline stage (recording, transcription, summarization, vault_save). Each stage has a status (pending, running, success, failed, skipped), an optional error message, and timing information.

This model should be reusable across the worker, UI, and vault storage layers.

## Acceptance Criteria

- [ ] `PipelineStatus` class defined in `src/gui/pipeline_status.py`
- [ ] Each stage tracks: status enum (pending/running/success/failed/skipped), error message (str or None), duration (float or None)
- [ ] `to_dict()` and `from_dict()` methods for serialization (JSON-compatible)
- [ ] `start_stage(name)`, `complete_stage(name)`, `fail_stage(name, error)`, `skip_stage(name)` convenience methods
- [ ] Model is importable and usable without GUI dependencies
