# BEAN-043: Comprehensive README Rewrite

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-043     |
| Title     | Comprehensive README Rewrite |
| Type      | enhancement |
| Priority  | P1 |
| Status    | Done         |
| Created   | 2026-02-13   |
| Started   | 2026-02-14   |
| Completed | 2026-02-14   |
| Duration  |              |

## Problem Statement

The current README.md is significantly outdated and misleading for both users and developers. A thorough audit found these issues:

**Incorrect installation instructions:**
- Lines 100-105 tell users to `cp .env.example .env` and set `OPENAI_API_KEY` in `.env` -- this was replaced by keyring-based storage in BEAN-004. The app now manages API keys through its Settings UI.
- Lines 119-123 tell users to `pip install torch whisper` separately -- torch and openai-whisper are already in `requirements.txt`.
- Line 109 says `python main.py` -- this is correct but the automated scripts reference `main_qt.py` in some places.

**Stale references to deleted/non-existent files:**
- Line 207: `python test_config.py` -- root-level test scripts are being deleted in BEAN-035
- Line 284: `python diagnose_audio.py` -- same, being deleted
- Line 221: `python tests/run_tests.py` -- references a test runner that may not reflect the actual pytest workflow

**Inaccurate claims:**
- Line 28: Claims "90%+ test coverage" -- currently 54 tests are failing (BEAN-031)
- Project structure tree (lines 166-186) is outdated: missing `export/`, `utils/` modules; shows files that don't exist

**Missing information for developers:**
- No architecture overview (module responsibilities, data flow, key classes)
- No explanation of the processing pipeline (record → transcribe → summarize → export)
- No mention of speaker diarization (BEAN-006, BEAN-007, BEAN-017, BEAN-025)
- No mention of prompt templates for summary generation (BEAN-011)
- No mention of auto-categorization (BEAN-020)
- No mention of keyring/encrypted API key storage (the actual current approach)
- No mention of the export system (markdown, SRT, text exports)
- No mention of checkpoint recording for crash recovery (BEAN-001)

**Missing for public repo:**
- No license badge (LICENSE file being added in BEAN-040)
- No badges for Python version, PySide6, etc.
- Contributing section is just 5 bullet points (detailed CONTRIBUTING.md exists separately)

## Goal

A publication-ready README that accurately reflects every feature, provides correct installation instructions, includes a full architecture section for developers, and serves as the definitive entry point for anyone discovering the project.

## Scope

### In Scope

- Complete rewrite of README.md with accurate content throughout
- **Installation section:** Correct instructions for both API and local Whisper modes, using keyring (not .env) for API keys, correct prerequisites (Python 3.8+, FFmpeg, PortAudio)
- **Features section:** All current features including diarization, prompt templates, auto-categorization, export formats, checkpoint recording, vault management
- **Architecture section:** Full module diagram, data flow description, key classes and their responsibilities, processing pipeline explanation
- **Developer section:** How to set up a dev environment, run tests (`pytest tests/`), lint (`flake8`), format (`black`, `isort`), type check (`mypy`), and contribute
- **Project structure:** Accurate tree reflecting all current modules (`src/gui/`, `src/audio/`, `src/transcription/`, `src/ai/`, `src/config/`, `src/export/`, `src/vault/`, `src/utils/`, `src/assets/`)
- **Security section:** Brief overview of security features (keyring, encryption, path validation, HTML escaping, file permissions) with link to SECURITY.md
- **Configuration section:** How to configure via the Settings UI (not .env), model selection, theme options
- **Testing section:** Correct pytest commands, test categories, coverage generation
- **Troubleshooting section:** Updated to reference correct tools and approaches
- **Badges:** License, Python version, GUI framework
- **Screenshots:** Placeholder references for app screenshots (actual screenshots out of scope)

### Out of Scope

- Updating SECURITY.md, CONTRIBUTING.md, or docs/CONFIGURATION.md (covered by BEAN-038)
- Creating an ARCHITECTURE.md file (architecture goes directly in README per user preference)
- Adding actual screenshots (requires running the app and capturing)
- Documenting the AI team/bean workflow (kept internal in CLAUDE.md)
- Updating the GitHub repository URL references (depends on final repo location)

## Acceptance Criteria

- [x] README.md contains zero references to `.env` for API key configuration
- [x] Installation instructions correctly describe keyring-based API key setup via Settings UI
- [x] Project structure tree matches actual `src/` directory layout
- [x] Architecture section describes all modules, their responsibilities, and the data flow pipeline
- [x] All features implemented since initial release are documented (diarization, prompt templates, auto-categorization, exports, checkpointing)
- [x] Testing section uses `pytest tests/` as the primary command (not `run_tests.py` or `test_config.py`)
- [x] No references to deleted files (`test_config.py`, `diagnose_audio.py`, `settings_window.py`)
- [x] Developer setup section includes lint, format, type check, and test commands
- [x] Security section accurately reflects current architecture (keyring, Fernet encryption, path validation)
- [x] Troubleshooting section provides actionable guidance without referencing deleted scripts
- [x] README renders correctly in GitHub markdown preview

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Audit current src/ to catalog all modules and key classes | developer | | DONE |
| 2 | Draft features section covering all implemented capabilities | developer | 1 | DONE |
| 3 | Write architecture section with module diagram and data flow | developer | 1 | DONE |
| 4 | Write correct installation instructions (API + local modes) | developer | | DONE |
| 5 | Write developer setup section (tests, lint, format, mypy) | developer | | DONE |
| 6 | Update project structure tree | developer | 1 | DONE |
| 7 | Write security overview section | developer | | DONE |
| 8 | Write configuration and troubleshooting sections | developer | | DONE |
| 9 | Assemble final README.md and verify markdown rendering | developer | 2-8 | DONE |
| 10 | Review for accuracy against actual codebase | tech-qa | 9 | DONE |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      | 10    |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

This bean coexists with BEAN-038 task 3, which does minimal targeted fixes to README stale references. This bean does a comprehensive ground-up rewrite. If this bean is completed first, BEAN-038 task 3 becomes a no-op (already fixed). If BEAN-038 runs first, this bean will overwrite those fixes with the full rewrite anyway. No conflict either way.

The architecture section should cover:
- **Recording pipeline:** `AudioRecorder` → checkpoint flush → WAV output
- **Transcription pipeline:** `WhisperService` (API or local) → transcript text
- **Summarization pipeline:** `Summarizer` → `PromptTemplateManager` → OpenAI → structured summary
- **Export pipeline:** `TranscriptionExporter` + `MarkdownGenerator` → SRT/TXT/MD files
- **Vault:** `VaultManager` (SQLite) → `VaultDialog` (browse/search/export)
- **Speaker diarization:** `SpeakerService` → auto-diarization + manual labeling
- **Configuration:** `SettingsManager` → keyring + encrypted config fallback
- **Security layers:** Path validation, HTML escaping, file permissions, parameterized SQL

Key classes to document: `ScribeVaultMainWindow`, `AudioRecorder`, `WhisperService`, `Summarizer`, `VaultManager`, `SettingsManager`, `VaultDialog`, `SummaryViewer`, `SpeakerService`, `TranscriptionExporter`, `MarkdownGenerator`, `CostEstimator`, `PromptTemplateManager`.

Depends on BEAN-040 (Add MIT License) — needs the LICENSE file to exist for the license badge.
