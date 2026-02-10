# Task 002: Update AudioRecorder to Use AudioSettings

## Owner
developer

## Depends On
task-001

## Status
TODO

## Description
Modify `src/audio/recorder.py` so `AudioRecorder` can accept an `AudioSettings` object and apply quality preset parameters plus input device selection.

### Changes
- Add optional `input_device_index` parameter to `__init__`
- Pass `input_device_index` to PyAudio stream open calls
- Pass `input_device_index` to FFmpeg device selection
- Ensure `get_audio_devices()` returns usable device list

### Acceptance Criteria
- AudioRecorder accepts and uses all audio settings (sample_rate, channels, chunk_size, input_device_index)
- Input device selection works in PyAudio stream creation
- get_audio_devices returns device info suitable for UI dropdown
