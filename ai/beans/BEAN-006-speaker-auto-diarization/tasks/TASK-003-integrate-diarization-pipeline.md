# TASK-003: Integrate Diarization into Transcription Pipeline

## Metadata

| Field     | Value        |
|-----------|--------------|
| Task      | TASK-003     |
| Bean      | BEAN-006     |
| Owner     | developer    |
| Priority  | 3            |
| Status    | TODO         |
| Depends   | TASK-001, TASK-002 |
| Started   | —            |
| Completed | —            |
| Duration  | —            |
| Tokens    | —            |

## Description

Update `src/transcription/whisper_service.py` to optionally run diarization after transcription. Add a new method `transcribe_with_diarization()` that:

1. Gets word-level timestamps from Whisper (API or local)
2. Runs `DiarizationService.diarize()` on the audio + timestamps
3. Returns both raw transcription and diarized transcription
4. Falls back to raw transcription if diarization fails

Must work with both OpenAI API and local Whisper backends.

## Acceptance Criteria

- [ ] `WhisperService.transcribe_with_diarization(audio_path)` method exists
- [ ] Returns dict with `transcription` (raw) and `diarized_transcription` (speaker-labeled) keys
- [ ] Works with OpenAI API backend (uses verbose_json for timestamps)
- [ ] Works with local Whisper backend (uses word_timestamps option)
- [ ] Falls back to unlabeled transcription if diarization fails (no crash)
- [ ] Respects `diarization_enabled` setting
