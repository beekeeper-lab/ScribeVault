# Task 004: Write tests for new export organization

**Owner:** Tech-QA
**Status:** TODO
**Depends On:** 001, 002, 003

## Description

Write comprehensive tests covering:
- `sanitize_title()` edge cases (special chars, empty, long titles, unicode)
- `create_unique_subfolder()` dedup logic
- MarkdownGenerator title-first filenames and subfolder creation
- Vault export subfolder creation and file naming

## Acceptance Criteria

- [ ] Tests for sanitize_title covering edge cases
- [ ] Tests for create_unique_subfolder with duplicate handling
- [ ] Tests for MarkdownGenerator new naming/subfolder behavior
- [ ] All existing tests still pass
