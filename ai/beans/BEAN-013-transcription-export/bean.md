# BEAN-013: Transcription Export

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-013     |
| Title     | Transcription Export |
| Type      | feature |
| Priority  | P2 |
| Status    | Done         |
| Owner     | team-lead    |
| Created   | 2026-02-10   |
| Started   | 2026-02-10 16:19 |
| Completed | 2026-02-10 16:30 |
| Duration  | ~11 min      |

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

- [x] Export to plain text (.txt) with speaker labels preserved
- [x] Export to markdown (.md) with proper formatting and metadata header
- [x] Export to SRT (.srt) if timestamp data available
- [x] Size warning shown for transcriptions >50KB
- [x] Export accessible from vault UI
- [x] Metadata header includes: title, date, duration, speakers (if identified)
- [x] New tests cover export format generation

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Design Transcription Exporter Module | architect | — | DONE |
| 2 | Implement TranscriptionExporter | developer | 1 | DONE |
| 3 | Wire Export to Vault UI | developer | 2 | DONE |
| 4 | Write Tests for Export Formats | tech-qa | 2 | DONE |
| 5 | Final Lint and Verification | tech-qa | 3, 4 | DONE |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      | 5     |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

No hard dependencies on other beans (but benefits from BEAN-003 vault export and BEAN-006 speaker diarization). Touches `src/export/markdown_generator.py`, `src/gui/qt_vault_dialog.py`.
