# TASK-004: Integrate Status Panel into Main Window

## Metadata

| Field     | Value        |
|-----------|--------------|
| Task      | TASK-004     |
| Title     | Integrate Status Panel into Main Window |
| Owner     | developer    |
| Priority  | 4            |
| Status    | DONE         |
| Depends   | TASK-002, TASK-003 |
| Started   | —            |
| Completed | —            |
| Duration  | —            |
| Tokens    | —            |

## Description

Integrate the `PipelineStatusPanel` into `ScribeVaultMainWindow`. Connect the worker's `stage_update` signal to the panel's `update_stage` method. Show the panel during pipeline processing and hide it when idle. Connect retry signals to trigger re-execution of failed stages.

## Acceptance Criteria

- [ ] Pipeline status panel is added to the main window layout (below progress bar or in a dedicated area)
- [ ] Panel is hidden by default and shown when processing starts
- [ ] Worker's `stage_update` signal is connected to panel's `update_stage` slot
- [ ] Panel's `retry_requested` signal triggers re-execution of the specified stage
- [ ] Retry creates a new worker that runs only the failed stage (not the entire pipeline)
- [ ] Panel remains visible after processing completes so user can see final status and retry failures
