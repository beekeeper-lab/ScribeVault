# Task 06: Write Tests for Re-generation and Templates

## Metadata

| Field | Value |
|-------|-------|
| Task ID | BEAN-011-T06 |
| Owner | tech-qa |
| Status | TODO |
| Depends On | T04, T05 |
| Blocks | T07 |

## Description

Write comprehensive tests covering prompt template management, summary re-generation, and summary history storage.

## Acceptance Criteria

- [ ] Test prompt template CRUD (create, read, update, delete)
- [ ] Test built-in templates are immutable
- [ ] Test summary re-generation with custom prompts (mocked OpenAI)
- [ ] Test summary history storage and retrieval
- [ ] Test style parameter fix for all categories
- [ ] All tests pass with `pytest tests/`
- [ ] Lint passes with `flake8 src/ tests/`

## Technical Notes

- Mock OpenAI API calls with `unittest.mock`
- Test file: `tests/test_prompt_templates.py` and `tests/test_summarizer.py`
- Cover edge cases: empty prompts, very long prompts, special characters in template names
