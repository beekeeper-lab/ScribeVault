"""
Diagnostic checks for the Test Settings feature.

Provides pure-logic functions that validate configuration settings
(API key, directories, microphone) and return structured results.
"""

import os
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import logging

logger = logging.getLogger(__name__)

# Timeout for API key validation (seconds)
API_CHECK_TIMEOUT = 10


@dataclass
class DiagnosticResult:
    """Result of a single diagnostic check."""
    name: str
    status: str  # "pass", "fail", "skip", "warning"
    message: str

    @property
    def passed(self) -> bool:
        return self.status == "pass"


def check_directory(path: str, label: str) -> DiagnosticResult:
    """Check that a directory exists and is writable.

    Args:
        path: Directory path to check.
        label: Human-readable label (e.g. "Recordings directory").

    Returns:
        DiagnosticResult with pass/fail status.
    """
    name = f"{label}"
    dir_path = Path(path)

    if not dir_path.exists():
        return DiagnosticResult(
            name=name,
            status="fail",
            message=f"Directory does not exist: {path}",
        )

    if not dir_path.is_dir():
        return DiagnosticResult(
            name=name,
            status="fail",
            message=f"Path is not a directory: {path}",
        )

    # Test write access by creating a temporary file
    try:
        fd, tmp_path = tempfile.mkstemp(dir=str(dir_path), prefix=".sv_test_")
        os.close(fd)
        os.unlink(tmp_path)
    except OSError as e:
        return DiagnosticResult(
            name=name,
            status="fail",
            message=f"Directory is not writable: {e}",
        )

    return DiagnosticResult(
        name=name,
        status="pass",
        message="Directory exists and is writable",
    )


def check_openai_api_key(
    settings_manager,
    needs_api_key: bool,
    timeout: float = API_CHECK_TIMEOUT,
) -> DiagnosticResult:
    """Validate the OpenAI API key with a live check.

    Args:
        settings_manager: SettingsManager instance.
        needs_api_key: Whether OpenAI services are configured.
        timeout: Maximum seconds to wait for the API call.

    Returns:
        DiagnosticResult with pass/fail/skip status.
    """
    name = "OpenAI API Key"

    if not needs_api_key:
        return DiagnosticResult(
            name=name,
            status="skip",
            message="Not required (local transcription, no AI summary)",
        )

    api_key = settings_manager.get_openai_api_key()
    if not api_key:
        return DiagnosticResult(
            name=name,
            status="fail",
            message="No API key configured",
        )

    # Run the live validation with a timeout
    result_holder: List[Optional[DiagnosticResult]] = [None]

    def _validate():
        try:
            is_valid, message = settings_manager.validate_openai_api_key_live(
                api_key
            )
            if is_valid:
                result_holder[0] = DiagnosticResult(
                    name=name, status="pass", message=message,
                )
            else:
                result_holder[0] = DiagnosticResult(
                    name=name, status="fail", message=message,
                )
        except Exception as e:
            result_holder[0] = DiagnosticResult(
                name=name, status="fail", message=f"Validation error: {e}",
            )

    thread = threading.Thread(target=_validate, daemon=True)
    thread.start()
    thread.join(timeout=timeout)

    if result_holder[0] is not None:
        return result_holder[0]

    return DiagnosticResult(
        name=name,
        status="fail",
        message=f"API check timed out after {timeout}s",
    )


def check_microphone(device_index: Optional[int] = None) -> DiagnosticResult:
    """Test microphone access by opening and closing a PyAudio stream.

    Args:
        device_index: Audio input device index, or None for system default.

    Returns:
        DiagnosticResult with pass/fail status.
    """
    name = "Microphone Access"

    try:
        import pyaudio
    except ImportError:
        return DiagnosticResult(
            name=name,
            status="fail",
            message="PyAudio is not installed",
        )

    pa = None
    stream = None
    try:
        pa = pyaudio.PyAudio()

        open_kwargs = {
            "format": pyaudio.paInt16,
            "channels": 1,
            "rate": 16000,
            "input": True,
            "frames_per_buffer": 1024,
        }
        if device_index is not None:
            open_kwargs["input_device_index"] = device_index

        stream = pa.open(**open_kwargs)
        stream.close()
        stream = None

        return DiagnosticResult(
            name=name,
            status="pass",
            message="Microphone is accessible",
        )
    except Exception as e:
        return DiagnosticResult(
            name=name,
            status="fail",
            message=f"Could not open microphone: {e}",
        )
    finally:
        if stream is not None:
            try:
                stream.close()
            except Exception:
                pass
        if pa is not None:
            try:
                pa.terminate()
            except Exception:
                pass


def run_all_checks(
    settings_manager,
    recordings_dir: str,
    vault_dir: str,
    device_index: Optional[int],
    needs_api_key: bool,
) -> List[DiagnosticResult]:
    """Run all diagnostic checks and return results.

    Args:
        settings_manager: SettingsManager instance.
        recordings_dir: Path to recordings directory.
        vault_dir: Path to vault directory.
        device_index: Audio input device index (None = default).
        needs_api_key: Whether an OpenAI API key is needed.

    Returns:
        List of DiagnosticResult for each check.
    """
    results = []

    results.append(check_directory(recordings_dir, "Recordings directory"))
    results.append(check_directory(vault_dir, "Vault directory"))
    results.append(
        check_openai_api_key(settings_manager, needs_api_key)
    )
    results.append(check_microphone(device_index))

    return results
