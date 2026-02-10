# Task 03: Add Summary History Storage

## Metadata

| Field | Value |
|-------|-------|
| Task ID | BEAN-011-T03 |
| Owner | developer |
| Status | TODO |
| Depends On | T01 |
| Blocks | T04, T05 |

## Description

Extend the vault storage to support multiple summaries per recording. Currently each recording stores only a single `summary` text field. We need to support a summary history so users can view previous and re-generated summaries.

## Acceptance Criteria

- [ ] Recordings can store multiple summaries with metadata
- [ ] Each summary entry has: content, template_name, prompt_used, created_at
- [ ] The most recent summary is still accessible via `recording['summary']` for backward compatibility
- [ ] Summary history is accessible via `recording['summary_history']`
- [ ] `VaultManager.add_summary()` method to append a new summary to a recording
- [ ] Tests cover summary history CRUD

## Technical Notes

- Store summary_history as a JSON field in the recordings table (like key_points/tags)
- Maintain backward compat: `summary` field always holds the latest summary text
- `add_summary(recording_id, content, template_name, prompt_used)` -> updates both summary and summary_history
