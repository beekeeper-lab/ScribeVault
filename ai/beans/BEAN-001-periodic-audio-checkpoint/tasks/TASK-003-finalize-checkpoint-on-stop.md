# TASK-003: Finalize Checkpoint on stop_recording

## Metadata

| Field     | Value          |
|-----------|----------------|
| Task      | TASK-003       |
| Bean      | BEAN-001       |
| Owner     | developer      |
| Priority  | 3              |
| Status    | TODO           |
| Depends   | TASK-002       |
| Started   | —              |
| Completed | —              |
| Duration  | —              |
| Tokens    | —              |

## Description

Modify `stop_recording()` to finalize the checkpoint file as the normal recording output. On stop: flush any remaining frames to the checkpoint, rename/move the checkpoint file to the final output path (removing the `.checkpoint` marker), and clean up any temporary state.

## Acceptance Criteria

- [ ] `stop_recording()` flushes all remaining frames to the checkpoint file
- [ ] Checkpoint file is renamed to the final recording output path
- [ ] No `.checkpoint` files remain after a clean stop
- [ ] The final WAV file is identical to what would have been produced without checkpointing
- [ ] The returned `Path` from `stop_recording()` points to the finalized file
