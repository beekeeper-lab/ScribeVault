# BEAN-006: Speaker Auto-Diarization

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-006     |
| Title     | Speaker Auto-Diarization |
| Type      | feature |
| Priority  | P1 |
| Status    | Done         |
| Owner     | team-lead    |
| Created   | 2026-02-10   |
| Started   | 2026-02-10 15:39 |
| Completed | 2026-02-10 15:48 |
| Duration  | ~9 min           |

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

- [x] Transcription output includes speaker labels (e.g., "Speaker 1: ...", "Speaker 2: ...")
- [x] Speaker changes are detected with reasonable accuracy (>80% for 2-3 speaker conversations)
- [x] Diarized transcription is stored in vault alongside raw transcription
- [x] Summary viewer displays speaker labels with visual distinction
- [x] Works with both API and local Whisper transcription
- [x] Graceful fallback to unlabeled transcription if diarization fails
- [x] New tests cover diarization output format

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Create DiarizationService module | developer | none | DONE |
| 2 | Add diarization configuration settings | developer | none | DONE |
| 3 | Integrate diarization into transcription pipeline | developer | 1, 2 | DONE |
| 4 | Update vault storage for diarized transcription | developer | 1 | DONE |
| 5 | Update markdown generator for speaker labels | developer | 1 | DONE |
| 6 | Update summary viewer with speaker display | developer | 5 | DONE |
| 7 | Write unit tests for diarization | tech-qa | 1, 3 | DONE |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      | 7     |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

No dependencies on other beans. Touches `src/transcription/whisper_service.py`, vault storage, and `src/gui/qt_summary_viewer.py`. May add a new dependency (pyannote-audio or similar).
