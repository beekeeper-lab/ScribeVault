# BEAN-030: Secure File & Directory Permissions

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-030     |
| Title     | Secure File & Directory Permissions |
| Type      | enhancement  |
| Priority  | P3           |
| Status    | Done         |
| Created   | 2026-02-10   |
| Started   | 2026-02-10   |
| Completed | 2026-02-10   |
| Duration  |              |

## Problem Statement

The application creates directories for recordings, vault data, summaries, and logs using default system umask permissions. On multi-user systems, this means other users may be able to read sensitive audio recordings, transcriptions, and summaries. The encrypted config file (`settings.py:424`) correctly uses `0o600`, but this practice is not applied consistently to other data directories and files.

## Goal

All application-created directories and files containing sensitive data use restrictive permissions, preventing access by other users on multi-user systems.

## Scope

### In Scope

- Set `0o700` permissions on `recordings/`, `vault/`, `summaries/` directories at creation time
- Set `0o600` permissions on the log file (`scribevault.log`)
- Set `0o600` permissions on newly created recording WAV files, markdown exports, and SQLite database
- Add a shared utility for creating directories and files with secure permissions

### Out of Scope

- Changing permissions on existing files (migration would be disruptive)
- Windows/macOS ACL handling (focus on POSIX chmod)
- Full-disk encryption or file-level encryption at rest

## Acceptance Criteria

- [x] `recordings/` directory is created with `0o700` permissions
- [x] `vault/` directory is created with `0o700` permissions
- [x] `summaries/` directory is created with `0o700` permissions
- [x] Log file is created with `0o600` permissions
- [x] New WAV recording files are created with `0o600` permissions
- [x] Unit tests verify directory and file permissions on creation (skipped on Windows)
- [x] `pytest tests/` passes, `flake8 src/ tests/` is clean

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Create secure directory/file creation utility | Developer | | Done |
| 2 | Apply to recordings directory and WAV files | Developer | 1 | Done |
| 3 | Apply to vault, summaries, and log file | Developer | 1 | Done |
| 4 | Write unit tests for permissions | Tech QA | 2, 3 | Done |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      | 4     |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

Key files: `src/audio/recorder.py` (line 86, recordings dir), `src/vault/manager.py` (vault dir), `src/export/markdown_generator.py` (summaries dir), `src/config/logging_config.py` (log file). The `os.makedirs(mode=0o700)` and `os.chmod()` patterns are straightforward. Windows does not support POSIX permissions, so the utility should be a no-op or skip on non-POSIX platforms.
