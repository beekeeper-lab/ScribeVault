# BEAN-014: Audio Recording Quality Settings

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-014     |
| Title     | Audio Recording Quality Settings |
| Type      | enhancement |
| Priority  | P3 |
| Status    | Done |
| Owner     | team-lead   |
| Created   | 2026-02-10   |
| Started   | 2026-02-10 16:19 |
| Completed | 2026-02-10 16:25 |
| Duration  | ~6 min       |

## Problem Statement

Audio recording parameters are hardcoded in `src/audio/recorder.py`:
- Sample rate: 44100 Hz (overkill for voice, wastes storage)
- Channels: 1 (mono only, no stereo option)
- Chunk size: 1024 (no tuning option)
- Input device: system default (no selection UI)

Users cannot choose between high-quality (music) and voice-optimized (smaller files) recording profiles, or select which microphone to use.

## Goal

Users can configure audio quality settings from the settings dialog, including sample rate, channels, and input device selection.

## Scope

### In Scope

- Add audio quality presets to settings: Voice (16kHz mono), Standard (44.1kHz mono), High Quality (44.1kHz stereo)
- Add input device selection dropdown (enumerate available audio devices)
- Store audio settings in config/settings.json
- Apply settings to recorder on next recording start
- Show estimated file size per minute for each quality preset

### Out of Scope

- Real-time audio quality switching during recording
- Audio format selection (WAV vs MP3 vs FLAC) -- keep WAV
- Audio post-processing (noise reduction, normalization)

## Acceptance Criteria

- [x] Settings dialog shows audio quality presets (Voice/Standard/High Quality)
- [x] Settings dialog shows input device dropdown with available devices
- [x] Selected quality preset applies to next recording
- [x] Selected input device applies to next recording
- [x] Estimated file size per minute shown for each preset
- [x] Settings persist across app restarts
- [x] New tests cover quality preset application and device enumeration

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Add AudioSettings dataclass to settings.py | developer | — | Done |
| 2 | Update AudioRecorder to use AudioSettings | developer | 1 | Done |
| 3 | Add Audio tab to Settings Dialog | developer | 1, 2 | Done |
| 4 | Write tests for audio quality settings | tech-qa | 1, 2 | Done |
| 5 | Lint, test, and verify | tech-qa | 1, 2, 3, 4 | Done |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      | 5     |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

No dependencies on other beans. Touches `src/audio/recorder.py`, `src/config/settings.py`, `src/gui/qt_settings_dialog.py`.
