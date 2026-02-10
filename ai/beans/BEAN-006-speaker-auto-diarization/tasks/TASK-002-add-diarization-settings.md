# TASK-002: Add Diarization Configuration Settings

## Metadata

| Field     | Value        |
|-----------|--------------|
| Task      | TASK-002     |
| Bean      | BEAN-006     |
| Owner     | developer    |
| Priority  | 2            |
| Status    | TODO         |
| Depends   | none         |
| Started   | —            |
| Completed | —            |
| Duration  | —            |
| Tokens    | —            |

## Description

Add diarization configuration to `src/config/settings.py` following the existing `TranscriptionSettings` and `SummarizationSettings` patterns. This allows users to enable/disable diarization and configure its behavior.

**Settings to add:**
- `diarization_enabled: bool` (default: True)
- `diarization_num_speakers: int` (default: 0 = auto-detect)
- `diarization_sensitivity: float` (default: 0.5, range 0.0-1.0)

## Acceptance Criteria

- [ ] `DiarizationSettings` dataclass exists in `src/config/settings.py`
- [ ] Default values are sensible (enabled by default, auto-detect speakers)
- [ ] Settings integrate with existing `SettingsManager` load/save
- [ ] Settings are accessible from `SettingsManager` instance
