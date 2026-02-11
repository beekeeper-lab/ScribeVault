# Task 001: Add WhisperService to VaultDialog

## Owner
Developer

## Depends On
(none)

## Description
Pass `whisper_service` to `VaultDialog.__init__()` and store it as `self.whisper_service`. Update the call site in `qt_main_window.py` to pass the service.

## Acceptance Criteria
- VaultDialog constructor accepts `whisper_service` parameter
- Main window passes `self.whisper_service` when creating VaultDialog
- Service stored as instance attribute

## Status
Done
