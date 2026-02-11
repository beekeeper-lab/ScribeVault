# Task 005: Align categorize_content() prompt to match valid category set

## Owner: Developer
## Depends On: 001
## Status: TODO

### Description
In `src/ai/summarizer.py` categorize_content():
- Update prompt to return `uncategorized` instead of `other`
- Update fallback returns from `"other"` to `"uncategorized"`

### Acceptance Criteria
- Prompt lists: meeting, lecture, interview, note, call, presentation, uncategorized
- Exception fallbacks return `uncategorized`
