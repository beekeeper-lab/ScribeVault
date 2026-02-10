# TASK-001: Create DiarizationService Module

## Metadata

| Field     | Value        |
|-----------|--------------|
| Task      | TASK-001     |
| Bean      | BEAN-006     |
| Owner     | developer    |
| Priority  | 1            |
| Status    | TODO         |
| Depends   | none         |
| Started   | —            |
| Completed | —            |
| Duration  | —            |
| Tokens    | —            |

## Description

Create a new `src/transcription/diarization.py` module containing the core speaker diarization logic. This module provides a `DiarizationService` class that takes audio and word-level timestamps as input and produces speaker-labeled segments.

**Approach:** Use simple audio feature extraction (MFCC/energy-based) with scipy spectral clustering to identify speaker changes. This avoids external auth tokens (like pyannote requires) while providing reasonable accuracy for 2-3 speaker conversations.

**Key classes/types:**
- `DiarizedSegment` — dataclass with `speaker: str`, `text: str`, `start: float`, `end: float`
- `DiarizationResult` — contains `segments: List[DiarizedSegment]`, `num_speakers: int`, helper methods
- `DiarizationService` — main service class with `diarize(audio_path, word_timestamps) -> DiarizationResult`

**Requirements:**
- Add `scipy` to `requirements.txt` (for spectral clustering)
- Handle mono and stereo audio
- Support auto-detecting number of speakers (2-6 range)
- Provide formatted output as "Speaker 1: text\nSpeaker 2: text\n..."
- Graceful error handling — return None or empty result on failure

## Acceptance Criteria

- [ ] `DiarizationService` class exists in `src/transcription/diarization.py`
- [ ] `diarize()` method accepts audio path and word timestamps, returns `DiarizationResult`
- [ ] `DiarizationResult.to_labeled_text()` returns formatted "Speaker N: ..." string
- [ ] Handles mono and stereo audio without crashing
- [ ] Returns None gracefully if audio cannot be processed
- [ ] `scipy` added to `requirements.txt`
