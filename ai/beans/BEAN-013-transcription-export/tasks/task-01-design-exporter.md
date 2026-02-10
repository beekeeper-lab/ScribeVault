# Task 01: Design Transcription Exporter Module

| Field      | Value          |
|------------|----------------|
| Owner      | architect      |
| Status     | TODO           |
| Depends On |                |

## Description

Design the `TranscriptionExporter` class interface that supports multiple export formats (TXT, MD, SRT). Define data structures for recording metadata and the export API.

## Acceptance Criteria

- [ ] Class interface defined with export methods for each format
- [ ] Recording metadata structure documented
- [ ] Size warning threshold (50KB) incorporated into design
- [ ] SRT format conditionally available based on timestamp data

## Notes

The existing `MarkdownGenerator` handles summary export. The new `TranscriptionExporter` focuses specifically on transcription text export with metadata headers. They are complementary — not replacing each other.
