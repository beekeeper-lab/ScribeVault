# BEAN-013: Transcription Export

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-013     |
| Title     | Transcription Export |
| Type      | feature |
| Priority  | P2 |
| Status    | Unapproved   |
| Created   | 2026-02-10   |
| Started   |              |
| Completed |              |
| Duration  |              |

## Problem Statement

There is limited ability to export transcriptions. The markdown generator (`src/export/markdown_generator.py`) creates a basic markdown file but:
1. No size limits -- huge transcriptions create unwieldy files
2. No format options (only markdown)
3. No timestamp linking between audio and transcription
4. Export is not accessible from the vault UI (export button is stubbed)

## Goal

Users can export transcriptions in multiple formats with sensible size handling and timestamp information.

## Scope

### In Scope

- Export transcription as plain text (.txt)
- Export transcription as markdown (.md) with improved formatting
- Export transcription as SRT subtitle format (.srt) if timestamps available
- Add size warnings for very long transcriptions (>50KB)
- Include metadata header in exports (recording date, duration, speakers)
- Wire export to vault UI (connect to BEAN-003's export button or add separate transcription export)

### Out of Scope

- PDF export
- Docx export
- Audio excerpt export (just text)
- Real-time collaborative editing

## Acceptance Criteria

- [ ] Export to plain text (.txt) with speaker labels preserved
- [ ] Export to markdown (.md) with proper formatting and metadata header
- [ ] Export to SRT (.srt) if timestamp data available
- [ ] Size warning shown for transcriptions >50KB
- [ ] Export accessible from vault UI
- [ ] Metadata header includes: title, date, duration, speakers (if identified)
- [ ] New tests cover export format generation

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

No hard dependencies on other beans (but benefits from BEAN-003 vault export and BEAN-006 speaker diarization). Touches `src/export/markdown_generator.py`, `src/gui/qt_vault_dialog.py`.
