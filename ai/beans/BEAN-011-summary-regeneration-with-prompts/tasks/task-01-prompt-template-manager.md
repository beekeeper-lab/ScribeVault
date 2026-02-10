# Task 01: Create Prompt Template Manager

## Metadata

| Field | Value |
|-------|-------|
| Task ID | BEAN-011-T01 |
| Owner | developer |
| Status | TODO |
| Depends On | - |
| Blocks | T02, T03, T04, T05 |

## Description

Create a new `PromptTemplateManager` class in `src/ai/prompt_templates.py` that manages built-in and custom prompt templates for summary generation.

## Acceptance Criteria

- [ ] `PromptTemplateManager` class created with built-in templates
- [ ] At least 5 built-in templates: Action Items, Key Decisions, Brief Summary, Detailed Notes, Meeting Minutes
- [ ] Custom template CRUD: save, load, delete, list
- [ ] Templates stored as JSON in `config/prompt_templates.json`
- [ ] Each template has: id, name, prompt_text, is_builtin, created_at
- [ ] Unit tests cover all template operations

## Technical Notes

- Built-in templates should be immutable (can't be deleted/modified)
- Custom templates stored in `config/prompt_templates.json`
- Template IDs: built-in use slugs (e.g., "action-items"), custom use timestamps
