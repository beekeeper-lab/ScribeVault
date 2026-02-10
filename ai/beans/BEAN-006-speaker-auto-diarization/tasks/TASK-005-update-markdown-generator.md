# TASK-005: Update Markdown Generator for Speaker Labels

## Metadata

| Field     | Value        |
|-----------|--------------|
| Task      | TASK-005     |
| Bean      | BEAN-006     |
| Owner     | developer    |
| Priority  | 5            |
| Status    | TODO         |
| Depends   | TASK-001     |
| Started   | —            |
| Completed | —            |
| Duration  | —            |
| Tokens    | —            |

## Description

Update `src/export/markdown_generator.py` to format diarized transcriptions with speaker labels in the markdown output. When diarized transcription is available, display it with speaker headings/formatting rather than the raw transcription block.

**Format in markdown:**
```
## Transcription

**Speaker 1:** Opening remarks about the project timeline...

**Speaker 2:** I think we should focus on the MVP first...

**Speaker 1:** Agreed. Let's prioritize the core features...
```

Fall back to existing code-block format when no diarized transcription is available.

## Acceptance Criteria

- [ ] Markdown output uses speaker-labeled format when diarized transcription is available
- [ ] Each speaker turn is formatted with bold speaker label
- [ ] Falls back to existing code-block format when no diarized transcription exists
- [ ] Generated markdown renders correctly
