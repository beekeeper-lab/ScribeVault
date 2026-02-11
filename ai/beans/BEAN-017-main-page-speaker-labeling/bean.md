# BEAN-017: Main Page Speaker Labeling

## Metadata

| Field     | Value        |
|-----------|--------------|
| **ID**        | BEAN-017     |
| **Title**     | Main Page Speaker Labeling |
| **Type**      | enhancement |
| **Priority**  | P1 |
| **Status**    | Approved     |
| **Created**   | 2026-02-10   |
| **Started**   | —            |
| **Completed** | —            |
| **Duration**  | —            |

## Problem Statement

After a recording is transcribed with speaker diarization, the detected speakers appear as generic labels (Speaker 1, Speaker 2, etc.) in the transcription text on the main page. Currently, to rename speakers, the user must open the Summary Viewer and navigate to the Speaker Labels tab. This is unintuitive — users see the generic labels right in front of them on the main page but have no way to fix them without navigating elsewhere.

## Goal

A collapsible "Name Speakers" section appears below the transcription on the main page when speakers are detected. Users can rename Speaker 1 → "Bob", Speaker 2 → "Sue", etc. directly from the main recording view, and the transcription text updates in real time.

## Scope

### In Scope

- Add a collapsible section below the transcription text area on the main page (`qt_main_window.py`)
- Reuse the existing `SpeakerPanel` widget from `src/gui/speaker_panel.py`
- Auto-show the collapsible section when the transcription contains speaker labels (e.g., `[Speaker 1]`)
- Keep the section collapsed by default to keep the main page clean
- Wire up `SpeakerPanel.transcription_updated` signal to update the main page transcription display
- Persist renamed speakers to the vault via the existing save mechanism

### Out of Scope

- Changing the `SpeakerPanel` widget itself (it already has rename, insert, save, revert functionality)
- Modifying the diarization logic
- Removing the Speaker Labels tab from the Summary Viewer (it should remain as an alternative)
- Adding new speaker detection algorithms

## Acceptance Criteria

- [ ] A collapsible "Name Speakers" section appears below the transcription on the main page
- [ ] The section is hidden when no speakers are detected in the transcription
- [ ] The section auto-appears (collapsed) when speakers are detected after transcription completes
- [ ] Expanding the section shows the existing `SpeakerPanel` UI (speaker list, rename, insert, preview)
- [ ] Renaming a speaker updates the transcription text displayed on the main page in real time
- [ ] Speaker changes can be saved to the vault from the main page
- [ ] Existing Speaker Labels tab in Summary Viewer continues to work independently
- [ ] Existing tests still pass

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Add collapsible QGroupBox with SpeakerPanel to main page layout below transcription | Developer | — | TODO |
| 2 | Wire transcription data into SpeakerPanel after diarization completes | Developer | 1 | TODO |
| 3 | Connect SpeakerPanel.transcription_updated signal to update main page transcript display | Developer | 1 | TODO |
| 4 | Add visibility logic: show section only when speakers detected, hide otherwise | Developer | 2 | TODO |
| 5 | Test speaker rename flow end-to-end on main page | Tech QA | 3, 4 | TODO |

## Telemetry

| Metric           | Value |
|------------------|-------|
| **Total Tasks**      | 5     |
| **Total Duration**   | —     |
| **Total Tokens In**  | —     |
| **Total Tokens Out** | —     |

## Notes

The existing `SpeakerPanel` in `src/gui/speaker_panel.py` already provides all the rename/insert/save/revert functionality. This bean is primarily about integrating it into the main page layout with a collapsible container. The `SpeakerPanel` is currently only used in `src/gui/qt_summary_viewer.py` as a tab. No dependencies on other beans — BEAN-007 (Speaker Manual Labeling UI) which created `SpeakerPanel` is already Done.
