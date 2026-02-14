# BEAN-040: Add MIT License

## Metadata

| Field     | Value        |
|-----------|--------------|
| ID        | BEAN-040     |
| Title     | Add MIT License |
| Type      | enhancement |
| Priority  | P1 |
| Status    | Done         |
| Created   | 2026-02-13   |
| Started   | 2026-02-13   |
| Completed | 2026-02-14   |
| Duration  | <1 day       |

## Problem Statement

The repository has no LICENSE file. Without a license, the default copyright applies -- no one has legal permission to use, modify, or distribute the code. This is a blocker for publishing as an open source project on GitHub.

The project uses PySide6 (LGPL-3.0), which is compatible with MIT licensing since PySide6 is used as a library dependency, not modified or redistributed directly.

## Goal

The repository has a proper MIT license file, making it legally clear that the code is open source and freely usable.

## Scope

### In Scope

- Add a `LICENSE` file with the MIT license text to the project root
- Use the copyright holder name "Beekeeper Lab" (or as specified by the project owner)
- Add a license badge to `README.md`

### Out of Scope

- Auditing all dependency licenses for compatibility (MIT is permissive and compatible with virtually all OSS licenses)
- Adding license headers to individual source files
- Creating a NOTICE file for third-party attributions

## Acceptance Criteria

- [x] `LICENSE` file exists at the project root with valid MIT license text
- [x] Copyright year and holder are correct
- [x] `README.md` includes a license section or badge
- [x] GitHub detects the license correctly (visible in repo sidebar)

## Tasks

| # | Task | Owner | Depends On | Status |
|---|------|-------|------------|--------|
| 1 | Create LICENSE file with MIT license text | developer | | DONE |
| 2 | Add license badge/section to README.md | developer | 1 | DONE |
| 3 | Verify GitHub license detection | tech-qa | 1 | DONE |

## Telemetry

| Metric           | Value |
|------------------|-------|
| Total Tasks      | 3     |
| Total Duration   | <1 day |
| Total Tokens In  |       |
| Total Tokens Out |       |

## Notes

MIT was chosen by the project owner. The standard MIT license text should use the current year (2026) and "Beekeeper Lab" as the copyright holder (confirm with owner if a different name is preferred).

The MIT license is compatible with PySide6's LGPL-3.0 because PySide6 is used as an unmodified dependency, not statically linked or redistributed as part of this project.
