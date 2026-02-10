# TASK-002: Integrate Retry into Summarizer

## Metadata

| Field     | Value       |
|-----------|-------------|
| Task      | TASK-002    |
| Bean      | BEAN-005    |
| Owner     | developer   |
| Priority  | 2           |
| Depends   | TASK-001    |
| Status    | Done        |
| Started   | 2026-02-10 15:56 |
| Completed | 2026-02-10 15:57 |
| Duration  | —           |
| Tokens    | —           |

## Description

Apply the shared retry utility to all 4 OpenAI API call sites in `src/ai/summarizer.py`:
1. `summarize_text` (line 59)
2. `extract_key_points` (line 85)
3. `categorize_content` (line 117)
4. `generate_structured_summary` (line 238)

## Implementation Details

- Import the retry utility from `src/utils/retry.py`
- Wrap each `self.client.chat.completions.create(...)` call with retry logic
- Add `import logging` and create a module-level logger
- Replace bare `print()` error statements with proper logging
- Ensure final failure surfaces a user-friendly message (not raw API traceback)
- Do not change the public API signatures of any methods

## Acceptance Criteria

- [ ] All 4 API call sites in summarizer use the shared retry wrapper
- [ ] Transient errors trigger automatic retry with exponential backoff
- [ ] Final failures return user-friendly error messages
- [ ] Module uses logging instead of print for error reporting
- [ ] Public method signatures are unchanged
