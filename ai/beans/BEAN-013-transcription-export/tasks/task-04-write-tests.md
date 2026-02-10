# Task 04: Write Tests for Export Formats

| Field      | Value          |
|------------|----------------|
| Owner      | tech-qa        |
| Status     | TODO           |
| Depends On | task-02        |

## Description

Create `tests/test_transcription_exporter.py` with comprehensive tests:
- TXT export content and formatting
- Markdown export content and formatting
- SRT export with and without timestamps
- Size warning threshold detection
- Metadata header content
- Edge cases: empty transcription, missing fields, special characters

## Acceptance Criteria

- [ ] Tests cover all three export formats
- [ ] Tests cover size warning logic
- [ ] Tests cover metadata header generation
- [ ] Tests cover edge cases
- [ ] All tests pass with `pytest tests/test_transcription_exporter.py`
