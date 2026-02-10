# Task 001: Add AudioSettings Dataclass

## Owner
developer

## Depends On
(none)

## Status
TODO

## Description
Add an `AudioSettings` dataclass to `src/config/settings.py` that defines audio quality presets and device selection. Integrate it into `AppSettings`.

### Audio Quality Presets
- **Voice**: 16000 Hz, 1 channel (mono), chunk_size 1024
- **Standard**: 44100 Hz, 1 channel (mono), chunk_size 1024
- **High Quality**: 44100 Hz, 2 channels (stereo), chunk_size 1024

### Fields
- `preset`: str ("voice", "standard", "high_quality") — default "standard"
- `sample_rate`: int — derived from preset or custom
- `channels`: int — derived from preset or custom
- `chunk_size`: int — default 1024
- `input_device_index`: Optional[int] — None means system default
- `input_device_name`: str — display name, default "System Default"

### Acceptance Criteria
- AudioSettings dataclass with validation
- Preset-to-parameters mapping helper
- Integrated into AppSettings
- File size estimation helper (bytes per minute for each preset)
- Settings load/save works with new audio section in JSON
