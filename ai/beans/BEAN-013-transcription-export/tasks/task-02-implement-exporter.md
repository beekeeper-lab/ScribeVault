# Task 02: Implement TranscriptionExporter

| Field      | Value          |
|------------|----------------|
| Owner      | developer      |
| Status     | TODO           |
| Depends On | task-01        |

## Description

Implement `src/export/transcription_exporter.py` with:
- `export_txt()`: Plain text export with speaker labels preserved, metadata header
- `export_markdown()`: Markdown export with proper formatting and metadata header
- `export_srt()`: SRT subtitle export (only if timestamp data available)
- Size warning detection for transcriptions >50KB
- Metadata header: title, date, duration, speakers (if identified)

## Acceptance Criteria

- [ ] TXT export with speaker labels and metadata header
- [ ] Markdown export with proper formatting and metadata header
- [ ] SRT export when timestamps available, graceful skip when not
- [ ] Size warning method for >50KB transcriptions
- [ ] Clean error handling
