# BEAN-006: Speaker Auto-Diarization

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-006     |
| Title     | Speaker Auto-Diarization |
| Type      | feature |
| Priority  | P1 |
| Status    | Approved   |
| Created   | 2026-02-10   |
| Started   |              |
| Completed |              |
| Duration  |              |

## Problem Statement

Transcriptions are currently a wall of undifferentiated text. For meetings, calls, and interviews, there is no indication of who said what. Speaker identification (diarization) is essential for making transcriptions useful — users need to know which participant made each statement.

## Goal

Automatically detect speaker changes during transcription and tag each segment with a speaker label (Speaker 1, Speaker 2, etc.) in the stored transcription.

## Scope

### In Scope

- Integrate a speaker diarization library (e.g., pyannote-audio, or Whisper's built-in word-level timestamps + clustering)
- Detect speaker changes and assign speaker labels (Speaker 1, Speaker 2, etc.)
- Store diarized transcription with speaker labels in the vault
- Display speaker-labeled transcription in the summary viewer
- Handle mono and stereo audio

### Out of Scope

- Real-time speaker identification during recording
- Voice fingerprinting / speaker recognition across recordings
- Manual speaker labeling UI (separate bean)
- Speaker name assignment (separate bean)

## Acceptance Criteria

- [ ] Transcription output includes speaker labels (e.g., "Speaker 1: ...", "Speaker 2: ...")
- [ ] Speaker changes are detected with reasonable accuracy (>80% for 2-3 speaker conversations)
- [ ] Diarized transcription is stored in vault alongside raw transcription
- [ ] Summary viewer displays speaker labels with visual distinction
- [ ] Works with both API and local Whisper transcription
- [ ] Graceful fallback to unlabeled transcription if diarization fails
- [ ] New tests cover diarization output format

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

No dependencies on other beans. Touches `src/transcription/whisper_service.py`, vault storage, and `src/gui/qt_summary_viewer.py`. May add a new dependency (pyannote-audio or similar).
