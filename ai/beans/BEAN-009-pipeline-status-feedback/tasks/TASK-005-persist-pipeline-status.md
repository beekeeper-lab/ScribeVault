# TASK-005: Persist Pipeline Status in Vault

## Metadata

| Field     | Value        |
|-----------|--------------|
| Task      | TASK-005     |
| Title     | Persist Pipeline Status in Vault |
| Owner     | developer    |
| Priority  | 5            |
| Status    | DONE         |
| Depends   | TASK-002     |
| Started   | —            |
| Completed | —            |
| Duration  | —            |
| Tokens    | —            |

## Description

Store the pipeline status alongside recording data in the vault. When the worker finishes, the pipeline status dict is saved. When viewing recordings in the vault dialog, the pipeline status is displayed. This enables users to see which stages succeeded/failed for historical recordings.

## Acceptance Criteria

- [ ] `VaultManager.add_recording()` accepts a `pipeline_status` parameter (JSON dict)
- [ ] Pipeline status is stored as a JSON field in the recordings table
- [ ] `VaultManager.get_recordings()` returns pipeline_status with each recording
- [ ] RecordingWorker passes pipeline_status to vault save
- [ ] Database migration handles adding the new column to existing databases
