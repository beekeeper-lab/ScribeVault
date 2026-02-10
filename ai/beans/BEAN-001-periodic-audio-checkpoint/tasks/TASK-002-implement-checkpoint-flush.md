# TASK-002: Implement Periodic Checkpoint Flush in AudioRecorder

## Metadata

| Field     | Value          |
|-----------|----------------|
| Task      | TASK-002       |
| Bean      | BEAN-001       |
| Owner     | developer      |
| Priority  | 2              |
| Status    | TODO           |
| Depends   | TASK-001       |
| Started   | —              |
| Completed | —              |
| Duration  | —              |
| Tokens    | —              |

## Description

Modify `AudioRecorder` to periodically flush accumulated audio frames to a temporary checkpoint WAV file on disk. A threading timer or frame-count check in `_audio_callback` triggers the flush at the configured interval. The checkpoint file is written incrementally — each flush appends new frames since the last flush. The checkpoint file must be a valid WAV file after each flush so it can be recovered if the app crashes.

## Acceptance Criteria

- [ ] A checkpoint `.wav` file is created in the recordings directory when recording starts
- [ ] Frames are flushed to the checkpoint file at the configured interval (default 30s)
- [ ] The checkpoint file is a valid, playable WAV file after each flush
- [ ] No audible glitches or gaps at checkpoint boundaries (frames are contiguous)
- [ ] Checkpoint filename includes a `.checkpoint` marker to distinguish from final recordings
