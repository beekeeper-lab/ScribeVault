# Task 02: Fix Summary Style Parameter Bug

## Metadata

| Field | Value |
|-------|-------|
| Task ID | BEAN-011-T02 |
| Owner | developer |
| Status | TODO |
| Depends On | T01 |
| Blocks | T04, T05 |

## Description

Fix the bug in `src/ai/summarizer.py` where the `style` parameter is ignored for meeting/call/interview categories. Currently `generate_summary_with_markdown()` (line 169-174) hardcodes `generate_structured_summary()` for these categories, ignoring the user's style choice.

Also add a new `summarize_with_prompt()` method that accepts a custom prompt string for re-generation.

## Acceptance Criteria

- [ ] Style parameter is respected for all recording categories
- [ ] When a custom prompt is provided, it overrides both style and category-based logic
- [ ] New `summarize_with_prompt(text, prompt)` method works with any prompt string
- [ ] Structured summary is still the default for meetings when no style/prompt override is specified
- [ ] Unit tests cover the bug fix and new method

## Technical Notes

- The fix should make structured summary the DEFAULT for meetings, but allow override via style or custom prompt
- `summarize_with_prompt()` sends the custom prompt as the system message to OpenAI
