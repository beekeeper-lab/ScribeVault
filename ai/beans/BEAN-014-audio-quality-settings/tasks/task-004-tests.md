# Task 004: Write Tests for Audio Quality Settings

## Owner
tech-qa

## Depends On
task-001, task-002

## Status
TODO

## Description
Write unit tests covering the AudioSettings dataclass, preset application, file size estimation, and device enumeration.

### Test Cases
- AudioSettings default values
- AudioSettings preset parameter mapping (voice, standard, high_quality)
- AudioSettings validation (invalid preset rejected)
- File size estimation per minute for each preset
- AudioRecorder accepts audio settings parameters
- Settings serialization/deserialization with audio section
- Device enumeration returns expected structure

### Acceptance Criteria
- All new tests pass
- Coverage for AudioSettings dataclass
- Coverage for preset-to-parameter mapping
- Coverage for file size estimation
- Existing tests still pass
