# Task 006: Test auto-categorization with and without summarizer

## Owner: Tech QA
## Depends On: 003, 005
## Status: TODO

### Description
- Update existing test assertions that expect `'other'` to expect `'uncategorized'`
- Add test for categorize_content() returning valid category
- Add test for categorize_content() returning unknown value → fallback to uncategorized
- Run full test suite and lint

### Acceptance Criteria
- All existing tests pass with updated category expectations
- New categorization tests pass
- flake8 clean
