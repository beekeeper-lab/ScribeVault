"""
Pipeline status panel widget for ScribeVault.

Displays real-time status indicators for each pipeline stage with
retry buttons for failed stages.
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from gui.constants import FONT_FAMILY

from gui.pipeline_status import (
    STATUS_PENDING, STATUS_RUNNING, STATUS_SUCCESS, STATUS_FAILED, STATUS_SKIPPED,
    STAGE_RECORDING, STAGE_TRANSCRIPTION, STAGE_SUMMARIZATION, STAGE_VAULT_SAVE,
    ALL_STAGES,
)


# Display names for stages
STAGE_LABELS = {
    STAGE_RECORDING: "Recording",
    STAGE_TRANSCRIPTION: "Transcription",
    STAGE_SUMMARIZATION: "Summarization",
    STAGE_VAULT_SAVE: "Vault Save",
}

# Status display config: (icon, color)
STATUS_DISPLAY = {
    STATUS_PENDING: ("--", "#888888"),
    STATUS_RUNNING: ("...", "#2196F3"),
    STATUS_SUCCESS: ("OK", "#4CAF50"),
    STATUS_FAILED: ("FAIL", "#F44336"),
    STATUS_SKIPPED: ("SKIP", "#FF9800"),
}


class StageIndicator(QFrame):
    """Individual stage status indicator widget."""

    retry_clicked = Signal(str)  # stage_name

    def __init__(self, stage_name: str, parent=None):
        super().__init__(parent)
        self.stage_name = stage_name
        self._status = STATUS_PENDING
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        # Stage label
        self.name_label = QLabel(STAGE_LABELS.get(self.stage_name, self.stage_name))
        self.name_label.setFont(QFont(FONT_FAMILY, 9, QFont.Bold))
        self.name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.name_label)

        # Status indicator
        self.status_label = QLabel("--")
        self.status_label.setFont(QFont(FONT_FAMILY, 9))
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Error label (hidden by default)
        self.error_label = QLabel("")
        self.error_label.setFont(QFont(FONT_FAMILY, 8))
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setMaximumWidth(180)
        self.error_label.setVisible(False)
        self.error_label.setStyleSheet("color: #F44336;")
        layout.addWidget(self.error_label)

        # Retry button (hidden by default)
        self.retry_button = QPushButton("Retry")
        self.retry_button.setFont(QFont(FONT_FAMILY, 8))
        self.retry_button.setMaximumWidth(60)
        self.retry_button.setVisible(False)
        self.retry_button.clicked.connect(lambda: self.retry_clicked.emit(self.stage_name))
        layout.addWidget(self.retry_button, alignment=Qt.AlignCenter)

        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self._apply_status_style()

    def update_status(self, status: str, error: str = ""):
        """Update the displayed status."""
        self._status = status
        icon, color = STATUS_DISPLAY.get(status, ("?", "#888888"))
        self.status_label.setText(icon)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

        # Show/hide error
        if status == STATUS_FAILED and error:
            self.error_label.setText(error[:120])
            self.error_label.setVisible(True)
            self.retry_button.setVisible(True)
        else:
            self.error_label.setVisible(False)
            self.retry_button.setVisible(False)

        self._apply_status_style()

    def _apply_status_style(self):
        """Apply border color based on status."""
        _, color = STATUS_DISPLAY.get(self._status, ("?", "#888888"))
        self.setStyleSheet(
            f"StageIndicator {{ border: 1px solid {color}; border-radius: 4px; "
            f"background-color: rgba(0,0,0,0.1); }}"
        )

    def reset(self):
        """Reset to pending state."""
        self.update_status(STATUS_PENDING)


class PipelineStatusPanel(QWidget):
    """Panel displaying pipeline stage status indicators."""

    retry_requested = Signal(str)  # stage_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._indicators = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(6)

        # Title
        title = QLabel("Pipeline:")
        title.setFont(QFont(FONT_FAMILY, 9, QFont.Bold))
        layout.addWidget(title)

        # Stage indicators
        for stage in ALL_STAGES:
            indicator = StageIndicator(stage)
            indicator.retry_clicked.connect(self.retry_requested.emit)
            self._indicators[stage] = indicator
            layout.addWidget(indicator)

        layout.addStretch()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

    def update_stage(self, stage_name: str, status: str, error: str = ""):
        """Update a stage indicator."""
        if stage_name in self._indicators:
            self._indicators[stage_name].update_status(status, error)

    def reset(self):
        """Reset all indicators to pending."""
        for indicator in self._indicators.values():
            indicator.reset()
