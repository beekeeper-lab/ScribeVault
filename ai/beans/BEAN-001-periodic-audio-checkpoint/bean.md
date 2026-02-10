# BEAN-001: Periodic Audio Checkpoint Saving

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-001     |
| Title     | Periodic Audio Checkpoint Saving |
| Type      | bug-fix |
| Priority  | P0 |
| Status    | Unapproved   |
| Created   | 2026-02-10   |
| Started   |              |
| Completed |              |
| Duration  |              |

## Problem Statement

The audio recorder (`src/audio/recorder.py`) accumulates all recording frames in an in-memory list (`self.frames`). Audio is only written to disk when `stop_recording()` is called. If the application crashes, the laptop shuts down, or the process is killed during recording, ALL audio data is lost. Users recording important meetings or lectures have no recovery path.

## Goal

Audio data is saved incrementally to disk during recording so that a crash or unexpected shutdown loses at most 30-60 seconds of audio, not the entire recording.

## Scope

### In Scope

- Implement periodic flush of audio frames to a temporary WAV file on disk (every 30-60 seconds)
- On `stop_recording()`, finalize the checkpoint file as the final recording
- On next app startup, detect and recover incomplete recordings from checkpoint files
- Add configurable checkpoint interval in settings

### Out of Scope

- Cloud backup of recordings
- Audio compression during recording (stick with WAV for checkpoints)
- Changes to the PySide6 UI beyond a recovery notification

## Acceptance Criteria

- [ ] Audio frames are flushed to a temp file at configurable intervals (default 30s)
- [ ] If app crashes mid-recording, checkpoint file contains all audio up to last flush
- [ ] On startup, app detects orphaned checkpoint files and offers recovery
- [ ] `stop_recording()` finalizes checkpoint into the normal recording output
- [ ] Existing tests still pass; new tests cover checkpoint creation and recovery
- [ ] No audible glitches or gaps at checkpoint boundaries in the final audio

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 |      |       |            | TODO   |
| 2 |      |       |            | TODO   |
| 3 |      |       |            | TODO   |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

No dependencies on other beans. Touches primarily `src/audio/recorder.py` and `src/config/settings.py`.
