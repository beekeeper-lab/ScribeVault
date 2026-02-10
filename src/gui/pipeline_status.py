"""
Pipeline status tracking for ScribeVault recording pipeline.

Tracks the status of each pipeline stage (recording, transcription,
summarization, vault_save) with per-stage error messages and timing.
"""

import time


# Stage status constants
STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"

# Pipeline stage names
STAGE_RECORDING = "recording"
STAGE_TRANSCRIPTION = "transcription"
STAGE_SUMMARIZATION = "summarization"
STAGE_VAULT_SAVE = "vault_save"

ALL_STAGES = [STAGE_RECORDING, STAGE_TRANSCRIPTION, STAGE_SUMMARIZATION, STAGE_VAULT_SAVE]


class PipelineStatus:
    """Tracks the status of each stage in the recording pipeline."""

    def __init__(self):
        self._stages = {}
        for stage in ALL_STAGES:
            self._stages[stage] = {
                "status": STATUS_PENDING,
                "error": None,
                "duration": None,
                "_start_time": None,
            }

    def start_stage(self, name: str) -> None:
        """Mark a stage as running and start its timer."""
        if name not in self._stages:
            raise ValueError(f"Unknown stage: {name}")
        self._stages[name]["status"] = STATUS_RUNNING
        self._stages[name]["error"] = None
        self._stages[name]["_start_time"] = time.monotonic()

    def complete_stage(self, name: str) -> None:
        """Mark a stage as successfully completed."""
        if name not in self._stages:
            raise ValueError(f"Unknown stage: {name}")
        stage = self._stages[name]
        stage["status"] = STATUS_SUCCESS
        stage["error"] = None
        if stage["_start_time"] is not None:
            stage["duration"] = round(time.monotonic() - stage["_start_time"], 2)
            stage["_start_time"] = None

    def fail_stage(self, name: str, error: str) -> None:
        """Mark a stage as failed with an error message."""
        if name not in self._stages:
            raise ValueError(f"Unknown stage: {name}")
        stage = self._stages[name]
        stage["status"] = STATUS_FAILED
        stage["error"] = str(error)
        if stage["_start_time"] is not None:
            stage["duration"] = round(time.monotonic() - stage["_start_time"], 2)
            stage["_start_time"] = None

    def skip_stage(self, name: str) -> None:
        """Mark a stage as skipped."""
        if name not in self._stages:
            raise ValueError(f"Unknown stage: {name}")
        self._stages[name]["status"] = STATUS_SKIPPED
        self._stages[name]["error"] = None
        self._stages[name]["_start_time"] = None

    def get_stage(self, name: str) -> dict:
        """Get status info for a stage (without internal fields)."""
        if name not in self._stages:
            raise ValueError(f"Unknown stage: {name}")
        stage = self._stages[name]
        return {
            "status": stage["status"],
            "error": stage["error"],
            "duration": stage["duration"],
        }

    def has_failures(self) -> bool:
        """Return True if any stage has failed."""
        return any(s["status"] == STATUS_FAILED for s in self._stages.values())

    def failed_stages(self) -> list:
        """Return list of stage names that failed."""
        return [name for name, s in self._stages.items() if s["status"] == STATUS_FAILED]

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dict."""
        result = {}
        for name, stage in self._stages.items():
            result[name] = {
                "status": stage["status"],
                "error": stage["error"],
                "duration": stage["duration"],
            }
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "PipelineStatus":
        """Deserialize from a dict."""
        ps = cls()
        for name in ALL_STAGES:
            if name in data:
                stage_data = data[name]
                ps._stages[name]["status"] = stage_data.get("status", STATUS_PENDING)
                ps._stages[name]["error"] = stage_data.get("error")
                ps._stages[name]["duration"] = stage_data.get("duration")
        return ps
