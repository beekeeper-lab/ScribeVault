# Task 002: Add Audio Playback to PySide6 Vault Dialog

| Field | Value |
|-------|-------|
| Task ID | BEAN-010-T002 |
| Owner | developer |
| Status | TODO |
| Depends On | T001 |
| Priority | P0 |

## Description

Add a "Play Audio" button to the PySide6 vault dialog's recording details panel and table controls. Port the `_play_audio()` method from CustomTkinter `main_window.py:1289-1310` which uses platform-specific subprocess calls (os.startfile on Windows, open on macOS, xdg-open on Linux).

## Acceptance Criteria

- [ ] Play Audio button appears in vault table controls
- [ ] Play Audio button appears in recording details panel
- [ ] Platform-specific audio playback using system default player
- [ ] Error handling for missing audio files
- [ ] Status bar feedback when playing audio
