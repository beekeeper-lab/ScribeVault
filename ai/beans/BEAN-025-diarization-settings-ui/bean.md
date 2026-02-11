# BEAN-025: Expose Diarization Settings in UI

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-025     |
| Title     | Expose Diarization Settings in UI |
| Type      | enhancement  |
| Priority  | P2           |
| Status    | Approved     |
| Created   | 2026-02-10   |
| Started   |              |
| Completed |              |
| Duration  |              |

## Problem Statement

Speaker diarization was implemented in BEAN-006, and the configuration layer supports three settings (enabled, num_speakers, sensitivity) via DiarizationSettings in src/config/settings.py. However, none of these settings are exposed in the Settings dialog UI. Users have no way to enable/disable diarization, set the expected number of speakers, or adjust sensitivity — they're stuck with whatever the defaults are (enabled=True, num_speakers=0/auto, sensitivity=0.5).

## Goal

Users can configure speaker diarization from the Settings dialog, including toggling it on/off, setting speaker count (auto or 2-6), and adjusting sensitivity.

## Scope

### In Scope

- Add diarization controls to the Settings dialog (likely in the Transcription tab or a new subsection)
- Enable/disable toggle checkbox
- Speaker count selector (0=auto, 2-6)
- Sensitivity slider (0.0-1.0) with descriptive labels
- Load and save diarization settings via SettingsManager
- Brief explanatory text about what each setting does

### Out of Scope

- Changes to the diarization algorithm itself
- Adding new diarization backends or libraries
- Real-time speaker count detection or preview
- Changes to how diarization results are displayed in transcripts

## Acceptance Criteria

- [ ] Diarization section is visible in the Settings dialog (Transcription tab or clearly labeled section)
- [ ] Enable/disable checkbox toggles diarization on/off
- [ ] Speaker count control allows selecting auto (0) or a specific count (2-6)
- [ ] Sensitivity control allows adjustment between 0.0 and 1.0 with descriptive labels (e.g., "Less splitting" / "More splitting")
- [ ] Settings are loaded from and saved to config/settings.json via SettingsManager
- [ ] Disabling diarization grays out the speaker count and sensitivity controls
- [ ] Existing tests pass; new tests cover UI save/load of diarization settings

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Design diarization section layout in Transcription tab | | | TODO |
| 2 | Add enable checkbox, speaker count spinner, sensitivity slider | | 1 | TODO |
| 3 | Wire controls to load/save DiarizationSettings | | 2 | TODO |
| 4 | Add descriptive labels and help text | | 2 | TODO |
| 5 | Write tests for settings save/load round-trip | | 3 | TODO |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      |       |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

- DiarizationSettings dataclass already exists at src/config/settings.py with full validation.
- Diarization requires scipy (optional dependency). The UI should indicate if scipy is not installed and diarization won't work.
- Related: BEAN-006 (Speaker Auto-Diarization) implemented the backend; this bean adds the UI controls.
