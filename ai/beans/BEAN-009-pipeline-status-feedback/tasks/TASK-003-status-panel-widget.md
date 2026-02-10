# TASK-003: Create Pipeline Status Panel Widget

## Metadata

| Field     | Value        |
|-----------|--------------|
| Task      | TASK-003     |
| Title     | Create Pipeline Status Panel Widget |
| Owner     | developer    |
| Priority  | 3            |
| Status    | DONE         |
| Depends   | TASK-001     |
| Started   | —            |
| Completed | —            |
| Duration  | —            |
| Tokens    | —            |

## Description

Create a PySide6 widget (`PipelineStatusPanel`) that displays the status of each pipeline stage as a horizontal row of status indicators. Each indicator shows the stage name, current status (icon + text), and error message if failed. The panel includes retry buttons for failed stages.

## Acceptance Criteria

- [ ] `PipelineStatusPanel` class in `src/gui/pipeline_status_panel.py`
- [ ] Shows 4 stage indicators: Recording, Transcription, Summarization, Vault Save
- [ ] Each indicator shows status: Pending (gray), Running (blue/animated), Success (green), Failed (red), Skipped (yellow)
- [ ] Failed stages display the specific error message text
- [ ] Failed stages show a "Retry" button
- [ ] Panel emits `retry_requested(str)` signal when a retry button is clicked (stage_name)
- [ ] Panel has `update_stage(stage_name, status, error)` method for external updates
- [ ] Panel has `reset()` method to return all stages to pending
