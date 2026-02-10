# TASK-002: Enhance RecordingWorker with Stage-Level Signals

## Metadata

| Field     | Value        |
|-----------|--------------|
| Task      | TASK-002     |
| Title     | Enhance RecordingWorker with Stage-Level Signals |
| Owner     | developer    |
| Priority  | 2            |
| Status    | DONE         |
| Depends   | TASK-001     |
| Started   | —            |
| Completed | —            |
| Duration  | —            |
| Tokens    | —            |

## Description

Modify `RecordingWorker` in `src/gui/qt_main_window.py` to use the `PipelineStatus` model and emit stage-level signals as each pipeline stage starts, completes, or fails. The worker should track per-stage status and include the full pipeline status in its result dict.

## Acceptance Criteria

- [ ] New signal `stage_update = Signal(str, str, str)` emitted for each stage transition (stage_name, status, error_or_empty)
- [ ] RecordingWorker creates a PipelineStatus instance and updates it as stages execute
- [ ] Each stage (recording, transcription, summarization, vault_save) emits stage_update on start, completion, or failure
- [ ] The finished result dict includes `pipeline_status` key with serialized status
- [ ] Failed stages do not prevent subsequent stages from running (existing behavior preserved)
