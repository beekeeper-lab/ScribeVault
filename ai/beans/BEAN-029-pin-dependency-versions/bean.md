# BEAN-029: Pin Dependency Versions

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-029     |
| Title     | Pin Dependency Versions |
| Type      | enhancement  |
| Priority  | P2           |
| Status    | Done         |
| Created   | 2026-02-10   |
| Started   | 2026-02-10   |
| Completed | 2026-02-10   |
| Duration  |              |

## Problem Statement

All dependencies in `requirements.txt` use `>=` (minimum version) pinning with no upper bounds (e.g., `openai>=1.0.0`). This means `pip install -r requirements.txt` could install any future major version, potentially introducing breaking API changes, regressions, or supply-chain vulnerabilities through compromised new releases. The `openai` library in particular has had breaking changes between major versions.

## Goal

Dependencies are pinned with bounded version ranges to prevent unexpected upgrades while still allowing patch-level updates for security fixes.

## Scope

### In Scope

- Add upper-bound version constraints to all dependencies in `requirements.txt` (e.g., `>=1.0.0,<2.0.0`)
- Optionally introduce `pip-compile` (pip-tools) to generate a lockfile (`requirements.lock`) with exact pinned versions
- Document the version update process in a comment at the top of `requirements.txt`

### Out of Scope

- Migrating to Poetry, PDM, or other dependency managers
- Automated dependency update tooling (Dependabot, Renovate)
- Auditing dependencies for known CVEs (separate effort)

## Acceptance Criteria

- [x] Every dependency in `requirements.txt` has an upper bound (e.g., `<N+1.0.0` for each major version)
- [x] A `requirements.lock` file exists with exact pinned versions for reproducible installs
- [x] `pip install -r requirements.txt` succeeds in a clean virtualenv
- [x] `pip install -r requirements.lock` succeeds and produces identical versions across runs
- [x] A comment in `requirements.txt` explains the pinning strategy and how to update

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Add upper bounds to requirements.txt | Developer | | Done |
| 2 | Set up pip-compile and generate requirements.lock | Developer | 1 | Done |
| 3 | Verify clean install with both files | Tech QA | 2 | Done |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      | 3     |
| Total Duration   |       |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

Key file: `requirements.txt`. Current dependencies include PySide6, pyaudio, openai, python-dotenv, Pillow, openai-whisper, torch, numpy, scipy, qtawesome, pyqtdarktheme. The `openai` package had a major breaking change between v0.x and v1.x; similar risk exists for other libraries.
