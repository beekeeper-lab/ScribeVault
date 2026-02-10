# TASK-004: Implement Orphaned Checkpoint Recovery

## Metadata

| Field     | Value          |
|-----------|----------------|
| Task      | TASK-004       |
| Bean      | BEAN-001       |
| Owner     | developer      |
| Priority  | 4              |
| Status    | TODO           |
| Depends   | TASK-002       |
| Started   | —              |
| Completed | —              |
| Duration  | —              |
| Tokens    | —              |

## Description

Add a recovery mechanism that detects orphaned checkpoint files (from crashes) on startup and offers to recover them as completed recordings. A class method or standalone function scans the recordings directory for `.checkpoint.wav` files. For each found, it validates the WAV structure and makes the file available for recovery.

## Acceptance Criteria

- [ ] A `recover_checkpoints(recordings_dir)` function scans for `*.checkpoint.wav` files
- [ ] Valid checkpoint files are renamed to normal recording files and returned as recovered
- [ ] Invalid/corrupt checkpoint files are logged and skipped (not deleted)
- [ ] Function returns a list of recovered file paths (empty list if none found)
- [ ] Recovery works correctly even if the app was killed mid-flush (partial WAV handling)
