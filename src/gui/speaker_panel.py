"""
Speaker management panel for ScribeVault PySide6 application.

Provides UI for viewing/renaming speakers and manually inserting
speaker labels into transcriptions.
"""

import logging
from typing import Optional, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit,
    QGroupBox, QMessageBox,
)
from PySide6.QtCore import Signal

from transcription.speaker_service import (
    parse_speakers,
    rename_speaker,
    insert_speaker_at_line,
)

logger = logging.getLogger(__name__)


class SpeakerPanel(QWidget):
    """Panel for managing speaker labels in transcriptions.

    Signals:
        transcription_updated(str): Emitted when the transcription
            text has been modified by a rename or insertion.
    """

    transcription_updated = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._transcription = ""
        self._original_transcription = ""
        self._recording_data: Optional[Dict] = None
        self._vault_manager = None
        self._speaker_rows: list = []

        self._setup_ui()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Speaker list section
        self._create_speaker_list_section(layout)

        # Manual insertion section
        self._create_manual_insert_section(layout)

        # Transcription preview section
        self._create_preview_section(layout)

        # Action buttons
        self._create_action_buttons(layout)

        layout.addStretch()

    def _create_speaker_list_section(self, parent_layout):
        group = QGroupBox("Detected Speakers")
        group.setStyleSheet(
            "QGroupBox { font-weight: bold; }"
        )
        self._speaker_list_layout = QVBoxLayout(group)

        self._no_speakers_label = QLabel(
            "No speakers detected. Use manual insertion below "
            "to add speaker labels."
        )
        self._no_speakers_label.setStyleSheet(
            "color: #888; font-style: italic; padding: 10px;"
        )
        self._no_speakers_label.setWordWrap(True)
        self._speaker_list_layout.addWidget(self._no_speakers_label)

        parent_layout.addWidget(group)

    def _create_manual_insert_section(self, parent_layout):
        group = QGroupBox("Insert Speaker Label")
        layout = QGridLayout(group)

        layout.addWidget(QLabel("Speaker Name:"), 0, 0)
        self._insert_name_input = QLineEdit()
        self._insert_name_input.setPlaceholderText(
            "Enter speaker name..."
        )
        layout.addWidget(self._insert_name_input, 0, 1)

        layout.addWidget(QLabel("At Line:"), 1, 0)
        self._insert_line_input = QLineEdit()
        self._insert_line_input.setPlaceholderText("Line number (1-based)")
        self._insert_line_input.setMaximumWidth(120)
        layout.addWidget(self._insert_line_input, 1, 1)

        insert_button = QPushButton("Insert Label")
        insert_button.setStyleSheet(
            "QPushButton { background-color: #0078d4; color: white; }"
        )
        insert_button.clicked.connect(self._on_insert_speaker)
        layout.addWidget(insert_button, 2, 0, 1, 2)

        parent_layout.addWidget(group)

    def _create_preview_section(self, parent_layout):
        group = QGroupBox("Transcription Preview")
        layout = QVBoxLayout(group)

        self._preview_text = QTextEdit()
        self._preview_text.setReadOnly(True)
        self._preview_text.setMaximumHeight(200)
        self._preview_text.setStyleSheet(
            "QTextEdit { background-color: #2b2b2b; border: 1px solid #555; }"
        )
        self._preview_text.setPlaceholderText(
            "Transcription will appear here..."
        )
        layout.addWidget(self._preview_text)

        parent_layout.addWidget(group)

    def _create_action_buttons(self, parent_layout):
        btn_layout = QHBoxLayout()

        self._save_button = QPushButton("Save Changes")
        self._save_button.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; }"
        )
        self._save_button.setEnabled(False)
        self._save_button.clicked.connect(self._on_save)
        btn_layout.addWidget(self._save_button)

        self._revert_button = QPushButton("Revert to Original")
        self._revert_button.setStyleSheet(
            "QPushButton { background-color: #666; color: white; }"
        )
        self._revert_button.setEnabled(False)
        self._revert_button.clicked.connect(self._on_revert)
        btn_layout.addWidget(self._revert_button)

        btn_layout.addStretch()

        parent_layout.addLayout(btn_layout)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_vault_manager(self, vault_manager):
        """Set the vault manager used to persist changes."""
        self._vault_manager = vault_manager

    def load_recording(self, recording_data: Dict):
        """Load a recording's transcription into the panel."""
        self._recording_data = recording_data
        self._transcription = recording_data.get("transcription", "") or ""
        self._original_transcription = (
            recording_data.get("original_transcription")
            or self._transcription
        )
        self._refresh_ui()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _refresh_ui(self):
        """Rebuild the speaker list and preview from current state."""
        self._clear_speaker_rows()
        speakers = parse_speakers(self._transcription)

        if speakers:
            self._no_speakers_label.hide()
            for name in speakers:
                self._add_speaker_row(name)
        else:
            self._no_speakers_label.show()

        self._preview_text.setPlainText(self._transcription)

        has_changes = self._transcription != self._original_transcription
        self._save_button.setEnabled(has_changes)
        self._revert_button.setEnabled(has_changes)

    def _clear_speaker_rows(self):
        """Remove all dynamic speaker row widgets."""
        for widgets in self._speaker_rows:
            for w in widgets:
                w.setParent(None)
                w.deleteLater()
        self._speaker_rows.clear()

    def _add_speaker_row(self, name: str):
        """Add a row with a label and editable name field."""
        row_layout = QHBoxLayout()

        label = QLabel("Speaker:")
        label.setStyleSheet("font-weight: bold; min-width: 60px;")

        name_input = QLineEdit(name)
        name_input.setMinimumWidth(150)

        rename_btn = QPushButton("Rename")
        rename_btn.setStyleSheet(
            "QPushButton { background-color: #0078d4; color: white; }"
        )
        rename_btn.clicked.connect(
            lambda checked=False, old=name, inp=name_input:
            self._on_rename_speaker(old, inp.text())
        )

        container = QWidget()
        container.setLayout(row_layout)
        row_layout.addWidget(label)
        row_layout.addWidget(name_input)
        row_layout.addWidget(rename_btn)
        row_layout.setContentsMargins(0, 2, 0, 2)

        self._speaker_list_layout.addWidget(container)
        self._speaker_rows.append([container])

    # ------------------------------------------------------------------
    # Slot handlers
    # ------------------------------------------------------------------

    def _on_rename_speaker(self, old_name: str, new_name: str):
        """Handle a speaker rename request."""
        new_name = new_name.strip()
        if not new_name:
            QMessageBox.warning(
                self, "Invalid Name", "Speaker name cannot be empty."
            )
            return

        if old_name == new_name:
            return

        self._transcription = rename_speaker(
            self._transcription, old_name, new_name
        )
        self._refresh_ui()
        self.transcription_updated.emit(self._transcription)
        logger.info(f"Renamed speaker '{old_name}' to '{new_name}'")

    def _on_insert_speaker(self):
        """Handle manual speaker label insertion."""
        name = self._insert_name_input.text().strip()
        if not name:
            QMessageBox.warning(
                self,
                "Missing Name",
                "Please enter a speaker name.",
            )
            return

        line_text = self._insert_line_input.text().strip()
        if not line_text:
            QMessageBox.warning(
                self,
                "Missing Line",
                "Please enter a line number.",
            )
            return

        try:
            line_num = int(line_text) - 1  # Convert to 0-based
        except ValueError:
            QMessageBox.warning(
                self,
                "Invalid Line",
                "Line number must be an integer.",
            )
            return

        if line_num < 0:
            QMessageBox.warning(
                self,
                "Invalid Line",
                "Line number must be 1 or greater.",
            )
            return

        self._transcription = insert_speaker_at_line(
            self._transcription, line_num, name
        )
        self._refresh_ui()
        self.transcription_updated.emit(self._transcription)
        self._insert_name_input.clear()
        self._insert_line_input.clear()
        logger.info(f"Inserted speaker '{name}' at line {line_num + 1}")

    def _on_save(self):
        """Save the updated transcription to the vault."""
        if not self._recording_data or not self._vault_manager:
            QMessageBox.warning(
                self,
                "Cannot Save",
                "No recording loaded or vault not connected.",
            )
            return

        recording_id = self._recording_data.get("id")
        if not recording_id:
            QMessageBox.warning(
                self, "Cannot Save", "Recording has no ID."
            )
            return

        try:
            self._vault_manager.update_recording(
                recording_id,
                transcription=self._transcription,
                original_transcription=self._original_transcription,
            )
            # Update local state
            self._recording_data["transcription"] = self._transcription
            self._recording_data[
                "original_transcription"
            ] = self._original_transcription

            self._refresh_ui()
            QMessageBox.information(
                self,
                "Saved",
                "Speaker labels saved successfully.",
            )
            logger.info(
                f"Saved speaker changes for recording {recording_id}"
            )
        except Exception as e:
            logger.error(f"Error saving speaker changes: {e}")
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save changes:\n{e}",
            )

    def _on_revert(self):
        """Revert to the original transcription."""
        reply = QMessageBox.question(
            self,
            "Confirm Revert",
            "Revert all speaker label changes to the original?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._transcription = self._original_transcription
            self._refresh_ui()
            self.transcription_updated.emit(self._transcription)
            logger.info("Reverted to original transcription")
