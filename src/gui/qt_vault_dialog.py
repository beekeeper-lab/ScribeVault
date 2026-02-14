"""
Vault dialog for ScribeVault PySide6 application.
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QWidget,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QSplitter,
    QGroupBox,
    QMessageBox,
    QFileDialog,
    QScrollArea,
    QFrame,
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, Slot

from vault.manager import VaultManager, VaultException
from gui.qt_summary_viewer import SummaryViewerDialog
from export.transcription_exporter import TranscriptionExporter
from export.utils import sanitize_title, create_unique_subfolder, validate_path_within
import logging

logger = logging.getLogger(__name__)


class RegenerationWorker(QThread):
    """Worker thread for summary re-generation."""

    finished = Signal(str, str)  # (summary, template_name)
    error = Signal(str)

    def __init__(
        self, summarizer_service, transcription, prompt, template_name=""
    ):
        super().__init__()
        self.summarizer_service = summarizer_service
        self.transcription = transcription
        self.prompt = prompt
        self.template_name = template_name

    def run(self):
        try:
            result = self.summarizer_service.summarize_with_prompt(
                self.transcription, self.prompt
            )
            if result:
                self.finished.emit(result, self.template_name)
            else:
                self.error.emit("Summarization returned no result")
        except Exception as e:
            self.error.emit(str(e))


class TranscriptionWorker(QThread):
    """Worker thread for on-demand transcription."""

    finished = Signal(str)  # transcription text
    error = Signal(str)

    def __init__(self, whisper_service, audio_path):
        super().__init__()
        self.whisper_service = whisper_service
        self.audio_path = audio_path

    def run(self):
        try:
            result = self.whisper_service.transcribe_with_diarization(
                self.audio_path
            )
            transcript = (
                result.get("diarized_transcription")
                or result.get("transcription")
            )
            if transcript:
                self.finished.emit(transcript)
            else:
                self.error.emit("Transcription returned no result")
        except Exception as e:
            self.error.emit(str(e))


class OnDemandSummarizationWorker(QThread):
    """Worker thread for on-demand summarization."""

    finished = Signal(dict)  # result dict with summary, markdown_path
    error = Signal(str)

    def __init__(self, summarizer_service, recording_data):
        super().__init__()
        self.summarizer_service = summarizer_service
        self.recording_data = recording_data

    def run(self):
        try:
            result = self.summarizer_service.generate_summary_with_markdown(
                self.recording_data
            )
            if result.get("summary"):
                self.finished.emit(result)
            else:
                error_msg = result.get("error", "Summarization failed")
                self.error.emit(error_msg)
        except Exception as e:
            self.error.emit(str(e))


class VaultDialog(QDialog):
    """Vault dialog for managing recordings."""

    def __init__(
        self,
        vault_manager: VaultManager,
        parent=None,
        summarizer_service=None,
        template_manager=None,
        whisper_service=None,
    ):
        super().__init__(parent)
        self.vault_manager = vault_manager
        self.summarizer_service = summarizer_service
        self.template_manager = template_manager
        self.whisper_service = whisper_service
        self.current_recordings = []
        self._regen_worker = None
        self._transcription_worker = None
        self._summarization_worker = None
        self._processing = False

        self.setup_ui()
        self.show_empty_details()  # Initialize with empty state
        self.load_recordings()

    def setup_ui(self):
        """Setup the vault dialog UI."""
        self.setWindowTitle("Recordings Vault")
        self.setMinimumSize(900, 600)
        self.resize(1100, 700)

        # Main layout
        layout = QVBoxLayout(self)

        # Header with title and controls (more compact)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 15, 20, 15)

        title_label = QLabel("📚 Recordings Vault")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Compact search and filter controls
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search recordings...")
        self.search_input.setMaximumWidth(200)
        self.search_input.textChanged.connect(self.filter_recordings)
        header_layout.addWidget(QLabel("Search:"))
        header_layout.addWidget(self.search_input)

        self.category_filter = QComboBox()
        self.category_filter.addItems(
            ["All", "meeting", "interview", "lecture",
             "note", "call", "presentation", "uncategorized"]
        )
        self.category_filter.setMaximumWidth(120)
        self.category_filter.currentTextChanged.connect(self.filter_recordings)
        header_layout.addWidget(QLabel("Category:"))
        header_layout.addWidget(self.category_filter)

        refresh_button = QPushButton("Refresh")
        refresh_button.setToolTip("Refresh recordings list")
        refresh_button.clicked.connect(self.load_recordings)
        header_layout.addWidget(refresh_button)

        layout.addLayout(header_layout)

        # Main content area with splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left side - recordings table
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Recordings count (more compact)
        self.count_label = QLabel("Total recordings: 0")
        self.count_label.setStyleSheet(
            "color: #888; font-size: 11px; padding: 3px;"
        )
        left_layout.addWidget(self.count_label)

        # Recordings table
        self.recordings_table = QTableWidget()
        self.setup_table()
        left_layout.addWidget(self.recordings_table)

        # Compact table controls
        table_controls = QHBoxLayout()
        table_controls.setContentsMargins(0, 5, 0, 5)

        self.transcribe_button = QPushButton("🎤 Transcribe")
        self.transcribe_button.setToolTip(
            "Transcribe audio for selected recording"
        )
        self.transcribe_button.clicked.connect(self.transcribe_selected)
        self.transcribe_button.setStyleSheet(
            "QPushButton { background-color: #7B1FA2;"
            " color: white; }"
        )
        self.transcribe_button.setMaximumHeight(30)
        self.transcribe_button.setEnabled(False)
        table_controls.addWidget(self.transcribe_button)

        self.summarize_button = QPushButton("🤖 Summarize")
        self.summarize_button.setToolTip(
            "Generate AI summary for selected recording"
        )
        self.summarize_button.clicked.connect(self.summarize_selected)
        self.summarize_button.setStyleSheet(
            "QPushButton { background-color: #1565C0;"
            " color: white; }"
        )
        self.summarize_button.setMaximumHeight(30)
        self.summarize_button.setEnabled(False)
        table_controls.addWidget(self.summarize_button)

        view_summary_button = QPushButton("🤖 View Summary")
        view_summary_button.setToolTip(
            "View AI summary for selected recording"
        )
        view_summary_button.clicked.connect(self.view_summary)
        view_summary_button.setStyleSheet(
            "QPushButton { background-color: #0078d4;" " color: white; }"
        )
        view_summary_button.setMaximumHeight(30)
        table_controls.addWidget(view_summary_button)

        delete_button = QPushButton("🗑️ Delete")
        delete_button.setToolTip("Delete selected recording")
        delete_button.clicked.connect(self.delete_recording)
        delete_button.setStyleSheet(
            "QPushButton { background-color: #d32f2f;" " color: white; }"
        )
        delete_button.setMaximumHeight(30)
        table_controls.addWidget(delete_button)

        export_button = QPushButton("📤 Export")
        export_button.setToolTip("Export selected recording")
        export_button.clicked.connect(self.export_recording)
        export_button.setMaximumHeight(30)
        table_controls.addWidget(export_button)

        play_button = QPushButton("🔊 Play Audio")
        play_button.setToolTip("Play audio file with system player")
        play_button.clicked.connect(self.play_audio)
        play_button.setStyleSheet(
            "QPushButton { background-color: #388E3C;" " color: white; }"
        )
        play_button.setMaximumHeight(30)
        table_controls.addWidget(play_button)

        table_controls.addStretch()

        view_files_button = QPushButton("📁 Open Vault")
        view_files_button.setToolTip("Open vault folder in file manager")
        view_files_button.clicked.connect(self.open_vault_folder)
        view_files_button.setMaximumHeight(30)
        table_controls.addWidget(view_files_button)

        left_layout.addLayout(table_controls)

        splitter.addWidget(left_widget)

        # Right side - recording details
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        details_label = QLabel("📋 Recording Details")
        details_label.setStyleSheet(
            "font-size: 14px; font-weight: bold;" " padding: 5px;"
        )
        right_layout.addWidget(details_label)

        # Details scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumWidth(350)

        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_widget)

        scroll_area.setWidget(self.details_widget)
        right_layout.addWidget(scroll_area)

        splitter.addWidget(right_widget)

        # Set splitter proportions (75% table, 25% details)
        splitter.setSizes([750, 350])
        layout.addWidget(splitter)

        # Small status bar at bottom
        status_frame = QFrame()
        status_frame.setMaximumHeight(30)
        status_frame.setStyleSheet(
            "background-color: #2b2b2b;" " border-top: 1px solid #555;"
        )

        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(10, 5, 10, 5)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        # Connection status indicator
        connection_label = QLabel("🟢 Vault Connected")
        connection_label.setStyleSheet("color: #4CAF50; font-size: 11px;")
        status_layout.addWidget(connection_label)

        layout.addWidget(status_frame)

    def setup_table(self):
        """Setup the recordings table."""
        headers = [
            "Title",
            "Category",
            "Duration",
            "Created",
            "Size",
        ]
        self.recordings_table.setColumnCount(len(headers))
        self.recordings_table.setHorizontalHeaderLabels(headers)

        # Configure table
        self.recordings_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.recordings_table.setSelectionMode(QTableWidget.SingleSelection)
        self.recordings_table.setAlternatingRowColors(True)
        self.recordings_table.setSortingEnabled(True)

        # Set column widths
        header = self.recordings_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.resizeSection(0, 200)  # Title
        header.resizeSection(1, 100)  # Category
        header.resizeSection(2, 80)  # Duration
        header.resizeSection(3, 150)  # Created
        header.resizeSection(4, 80)  # Size

        # Connect selection change
        self.recordings_table.itemSelectionChanged.connect(
            self.show_recording_details
        )
        logger.info(
            "Connected table selection change" " to show_recording_details"
        )

    def load_recordings(self):
        """Load recordings from the vault."""
        try:
            self.current_recordings = self.vault_manager.get_recordings()
            self.populate_table(self.current_recordings)
            self.update_count_label(len(self.current_recordings))
            self.update_status(
                f"Loaded {len(self.current_recordings)}" " recordings"
            )

        except VaultException as e:
            logger.error(f"Error loading recordings: {e}")
            QMessageBox.warning(
                self, "Vault Error", f"Failed to load recordings: {e}"
            )
            self.update_status("Error loading recordings")

    def populate_table(self, recordings: List[Dict]):
        """Populate the table with recordings."""
        self.recordings_table.setRowCount(len(recordings))

        for row, recording in enumerate(recordings):
            # Title
            title = recording.get("title", "Untitled")
            if not title:
                title = recording.get("filename", "Unknown")
            self.recordings_table.setItem(row, 0, QTableWidgetItem(title))

            # Category
            category = recording.get("category", "other")
            self.recordings_table.setItem(
                row, 1, QTableWidgetItem(category.title())
            )

            # Duration
            duration = recording.get("duration", 0)
            duration_str = self.format_duration(duration)
            self.recordings_table.setItem(
                row, 2, QTableWidgetItem(duration_str)
            )

            # Created date
            created_at = recording.get("created_at", "")
            if created_at:
                try:
                    # Parse and format datetime
                    if isinstance(created_at, str):
                        dt = datetime.fromisoformat(
                            created_at.replace("Z", "+00:00")
                        )
                    else:
                        dt = created_at
                    created_str = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    created_str = str(created_at)
            else:
                created_str = "Unknown"
            self.recordings_table.setItem(
                row, 3, QTableWidgetItem(created_str)
            )

            # File size
            file_size = recording.get("file_size", 0)
            size_str = self.format_file_size(file_size)
            self.recordings_table.setItem(row, 4, QTableWidgetItem(size_str))

            # Store recording data in first item
            title_item = self.recordings_table.item(row, 0)
            title_item.setData(Qt.UserRole, recording)
            logger.debug(
                "Stored recording data for row %d: %s",
                row,
                recording.get("filename", "Unknown"),
            )

    def filter_recordings(self):
        """Filter recordings based on search and category."""
        search_text = self.search_input.text().lower()
        category_filter = self.category_filter.currentText()

        filtered_recordings = []

        for recording in self.current_recordings:
            # Check category filter
            if category_filter != "All":
                rec_cat = recording.get("category", "other")
                if rec_cat != category_filter:
                    continue

            # Check search text
            if search_text:
                searchable_text = " ".join(
                    [
                        recording.get("title") or "",
                        recording.get("description") or "",
                        recording.get("filename") or "",
                        recording.get("transcription") or "",
                    ]
                ).lower()

                if search_text not in searchable_text:
                    continue

            filtered_recordings.append(recording)

        self.populate_table(filtered_recordings)
        self.update_count_label(len(filtered_recordings))

        # Show empty details if no recordings match
        if not filtered_recordings:
            self.show_empty_details()

    def show_recording_details(self):
        """Show details for the selected recording."""
        current_row = self.recordings_table.currentRow()

        # Clear previous details properly
        while self.details_layout.count():
            child = self.details_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if current_row < 0:
            logger.debug("No row selected, showing empty state")
            self._update_processing_buttons(None)
            self.show_empty_details()
            return

        # Get recording data
        title_item = self.recordings_table.item(current_row, 0)
        if not title_item:
            logger.debug("No title item found, showing empty state")
            self._update_processing_buttons(None)
            self.show_empty_details()
            return

        recording = title_item.data(Qt.UserRole)
        if not recording:
            logger.debug("No recording data found," " showing empty state")
            self._update_processing_buttons(None)
            self.show_empty_details()
            return

        logger.info(
            "Showing details for recording: %s",
            recording.get("filename", "Unknown"),
        )

        # Update toolbar button states
        self._update_processing_buttons(recording)

        # Create details widgets
        info_items = [
            ("Recording ID", recording.get("id", "N/A")),
            ("Title", recording.get("title", "Untitled")),
            ("Filename", recording.get("filename", "Unknown")),
            ("Category", recording.get("category", "other").title()),
            ("Duration", self.format_duration(recording.get("duration", 0))),
            (
                "File Size",
                self.format_file_size(recording.get("file_size", 0)),
            ),
            ("Created", recording.get("created_at", "Unknown")),
        ]
        self.create_detail_section("📝 Basic Information", info_items)

        # Action buttons for the selected recording
        actions_group = QGroupBox("Actions")
        actions_layout = QHBoxLayout(actions_group)

        play_btn = QPushButton("🔊 Play Audio")
        play_btn.clicked.connect(self.play_audio)
        play_btn.setStyleSheet(
            "QPushButton { background-color: #388E3C;" " color: white; }"
        )
        actions_layout.addWidget(play_btn)

        edit_btn = QPushButton("✏️ Edit")
        edit_btn.clicked.connect(self.edit_recording)
        actions_layout.addWidget(edit_btn)

        summary_btn = QPushButton("🤖 Summary")
        summary_btn.clicked.connect(self.view_summary)
        summary_btn.setStyleSheet(
            "QPushButton { background-color: #0078d4;" " color: white; }"
        )
        actions_layout.addWidget(summary_btn)

        # Detail panel Transcribe button
        has_audio = bool(
            self.vault_manager.get_audio_path(recording)
        )
        has_transcript = bool(
            recording.get("transcription", "").strip()
            if recording.get("transcription")
            else False
        )
        has_summary = bool(
            recording.get("summary", "").strip()
            if recording.get("summary")
            else False
        )

        detail_transcribe_btn = QPushButton("🎤 Transcribe")
        detail_transcribe_btn.clicked.connect(
            self.transcribe_selected
        )
        detail_transcribe_btn.setStyleSheet(
            "QPushButton { background-color: #7B1FA2;"
            " color: white; }"
        )
        detail_transcribe_btn.setEnabled(
            has_audio and not has_transcript
            and not self._processing
        )
        actions_layout.addWidget(detail_transcribe_btn)

        detail_summarize_btn = QPushButton("🤖 Summarize")
        detail_summarize_btn.clicked.connect(
            self.summarize_selected
        )
        detail_summarize_btn.setStyleSheet(
            "QPushButton { background-color: #1565C0;"
            " color: white; }"
        )
        detail_summarize_btn.setEnabled(
            has_audio and not has_summary
            and not self._processing
        )
        actions_layout.addWidget(detail_summarize_btn)

        self.details_layout.addWidget(actions_group)

        if recording.get("description"):
            self.create_text_section(
                "📋 Description",
                recording["description"],
            )

        if recording.get("transcription"):
            self.create_text_section(
                "🎤 Transcription",
                recording["transcription"],
            )

        if recording.get("summary"):
            self.create_text_section(
                "🤖 AI Summary",
                recording["summary"],
            )

        if recording.get("key_points"):
            key_points_text = "\n".join(
                [f"• {point}" for point in recording["key_points"]]
            )
            self.create_text_section("🔑 Key Points", key_points_text)

        if recording.get("tags"):
            tags_text = ", ".join(recording["tags"])
            self.create_detail_section("🏷️ Tags", [("Tags", tags_text)])

        self.details_layout.addStretch()

    def show_empty_details(self):
        """Show empty state when no recording is selected."""
        no_selection_label = QLabel("Select a recording to view details")
        no_selection_label.setAlignment(Qt.AlignCenter)
        no_selection_label.setStyleSheet(
            "color: #888; font-style: italic;" " padding: 20px;"
        )
        self.details_layout.addWidget(no_selection_label)
        self.details_layout.addStretch()

    def create_detail_section(self, title: str, items: List[tuple]):
        """Create a detail section with key-value pairs."""
        group = QGroupBox(title)
        layout = QGridLayout(group)

        for row, (key, value) in enumerate(items):
            key_label = QLabel(f"{key}:")
            key_label.setStyleSheet("font-weight: bold;")
            layout.addWidget(key_label, row, 0)

            value_label = QLabel(str(value) if value else "N/A")
            value_label.setWordWrap(True)
            layout.addWidget(value_label, row, 1)

        self.details_layout.addWidget(group)

    def create_text_section(self, title: str, text: str):
        """Create a text section with a text edit."""
        group = QGroupBox(title)
        layout = QVBoxLayout(group)

        text_edit = QTextEdit()
        text_edit.setPlainText(text)
        text_edit.setReadOnly(True)
        text_edit.setMaximumHeight(150)
        text_edit.setStyleSheet(
            "background-color: #2b2b2b;" " border: 1px solid #555;"
        )

        layout.addWidget(text_edit)
        self.details_layout.addWidget(group)

    def view_summary(self):
        """View AI summary for the selected recording."""
        current_row = self.recordings_table.currentRow()
        if current_row < 0:
            QMessageBox.information(
                self,
                "No Selection",
                "Please select a recording" " to view its summary.",
            )
            return

        title_item = self.recordings_table.item(current_row, 0)
        recording = title_item.data(Qt.UserRole)

        if not recording:
            QMessageBox.warning(
                self, "Error", "Could not retrieve recording data."
            )
            return

        # Check if there's a summary or markdown to show
        has_summary = recording.get("summary")
        has_markdown = recording.get("markdown_path")
        if not has_summary and not has_markdown:
            rec_title = recording.get("title", "Untitled")
            QMessageBox.information(
                self,
                "No Summary Available",
                "No AI summary or markdown file available"
                f" for recording '{rec_title}'.",
            )
            return

        try:
            # Create and show summary viewer
            summary_viewer = SummaryViewerDialog(
                self,
                vault_manager=self.vault_manager,
                template_manager=self.template_manager,
            )
            summary_viewer.load_recording_data(
                recording, recording.get("markdown_path")
            )

            # Connect re-generation signal
            self._current_viewer = summary_viewer
            self._current_recording = recording
            summary_viewer.regenerate_requested.connect(
                self._handle_regeneration_request
            )

            summary_viewer.exec()

        except Exception as e:
            logger.error(f"Error showing summary viewer: {e}")
            QMessageBox.critical(
                self,
                "Summary Viewer Error",
                f"Failed to open summary viewer: {e}",
            )

    @Slot(str, str)
    def _handle_regeneration_request(self, prompt_text, template_name):
        """Handle a re-generation request from viewer."""
        if not self.summarizer_service:
            viewer = getattr(self, "_current_viewer", None)
            if viewer:
                viewer.on_regeneration_error(
                    "Summarizer service not available."
                    " Check API key configuration."
                )
            return

        recording = getattr(self, "_current_recording", None)
        if not recording:
            return

        transcription = recording.get("transcription", "")
        if not transcription or not transcription.strip():
            viewer = getattr(self, "_current_viewer", None)
            if viewer:
                viewer.on_regeneration_error(
                    "No transcription available" " for this recording."
                )
            return

        # Run in worker thread
        self._regen_worker = RegenerationWorker(
            self.summarizer_service, transcription, prompt_text, template_name
        )
        self._regen_worker.finished.connect(self._on_regeneration_finished)
        self._regen_worker.error.connect(self._on_regeneration_error)
        self._regen_worker.start()

    @Slot(str, str)
    def _on_regeneration_finished(self, new_summary, template_name):
        """Handle successful re-generation."""
        recording = getattr(self, "_current_recording", None)
        if recording and recording.get("id"):
            try:
                self.vault_manager.add_summary(
                    recording["id"],
                    new_summary,
                    template_name=template_name,
                    prompt_used="",
                )
                # Update the in-memory recording data
                recording["summary"] = new_summary
            except Exception as e:
                logger.error("Failed to store re-generated" f" summary: {e}")

        viewer = getattr(self, "_current_viewer", None)
        if viewer:
            viewer.on_regeneration_complete(new_summary, template_name)

        self.update_status("Summary re-generated successfully")

    @Slot(str)
    def _on_regeneration_error(self, error_msg):
        """Handle re-generation error."""
        viewer = getattr(self, "_current_viewer", None)
        if viewer:
            viewer.on_regeneration_error(error_msg)
        self.update_status("Summary re-generation failed")

    def _get_selected_recording(self):
        """Get the currently selected recording dict."""
        current_row = self.recordings_table.currentRow()
        if current_row < 0:
            return None
        title_item = self.recordings_table.item(current_row, 0)
        if not title_item:
            return None
        return title_item.data(Qt.UserRole)

    def _update_processing_buttons(self, recording):
        """Enable/disable Transcribe and Summarize toolbar buttons."""
        if recording is None or self._processing:
            self.transcribe_button.setEnabled(False)
            self.summarize_button.setEnabled(False)
            return

        has_audio = bool(
            self.vault_manager.get_audio_path(recording)
        )
        has_transcript = bool(
            recording.get("transcription", "").strip()
            if recording.get("transcription")
            else False
        )
        has_summary = bool(
            recording.get("summary", "").strip()
            if recording.get("summary")
            else False
        )

        # Transcribe: enabled if audio exists and no transcript
        self.transcribe_button.setEnabled(
            has_audio and not has_transcript
        )
        # Summarize: enabled if audio exists and no summary
        # (will auto-chain transcription if needed)
        self.summarize_button.setEnabled(
            has_audio and not has_summary
        )

    def _set_processing(self, active):
        """Set processing state and update buttons."""
        self._processing = active
        recording = self._get_selected_recording()
        self._update_processing_buttons(recording)

    def transcribe_selected(self):
        """Transcribe the selected recording on-demand."""
        recording = self._get_selected_recording()
        if not recording:
            QMessageBox.information(
                self,
                "No Selection",
                "Please select a recording to transcribe.",
            )
            return

        if not self.whisper_service:
            QMessageBox.warning(
                self,
                "Service Unavailable",
                "Transcription service is not available."
                " Check your configuration.",
            )
            return

        audio_path = self.vault_manager.get_audio_path(recording)
        if not audio_path:
            QMessageBox.warning(
                self,
                "Audio Not Found",
                "Audio file not found on disk for"
                f" '{recording.get('title', 'Untitled')}'.",
            )
            return

        self._set_processing(True)
        self.update_status("Transcribing...")

        self._transcription_worker = TranscriptionWorker(
            self.whisper_service, audio_path
        )
        self._transcription_worker.finished.connect(
            self._on_transcription_finished
        )
        self._transcription_worker.error.connect(
            self._on_transcription_error
        )
        self._transcription_worker.start()

    @Slot(str)
    def _on_transcription_finished(self, transcript):
        """Handle successful transcription."""
        recording = self._get_selected_recording()
        if recording and recording.get("id"):
            try:
                self.vault_manager.update_recording(
                    recording["id"],
                    transcription=transcript,
                )
                recording["transcription"] = transcript
            except Exception as e:
                logger.error(
                    "Failed to store transcription: %s", e
                )

        self._set_processing(False)
        self.update_status("Transcription complete")
        self.show_recording_details()

    @Slot(str)
    def _on_transcription_error(self, error_msg):
        """Handle transcription error."""
        self._set_processing(False)
        self.update_status("Transcription failed")
        QMessageBox.critical(
            self,
            "Transcription Error",
            f"Failed to transcribe recording: {error_msg}",
        )

    def summarize_selected(self):
        """Summarize the selected recording on-demand."""
        recording = self._get_selected_recording()
        if not recording:
            QMessageBox.information(
                self,
                "No Selection",
                "Please select a recording to summarize.",
            )
            return

        if not self.summarizer_service:
            QMessageBox.warning(
                self,
                "Service Unavailable",
                "Summarization service is not available."
                " Check your API key configuration.",
            )
            return

        audio_path = self.vault_manager.get_audio_path(recording)
        if not audio_path:
            QMessageBox.warning(
                self,
                "Audio Not Found",
                "Audio file not found on disk for"
                f" '{recording.get('title', 'Untitled')}'.",
            )
            return

        has_transcript = bool(
            recording.get("transcription", "").strip()
            if recording.get("transcription")
            else False
        )

        if not has_transcript:
            # Auto-chain: transcribe first, then summarize
            if not self.whisper_service:
                QMessageBox.warning(
                    self,
                    "Service Unavailable",
                    "Transcription service is not available."
                    " A transcript is required before"
                    " summarization.",
                )
                return

            self._set_processing(True)
            self.update_status(
                "Transcribing before summarization..."
            )

            self._transcription_worker = TranscriptionWorker(
                self.whisper_service, audio_path
            )
            self._transcription_worker.finished.connect(
                self._on_chain_transcription_finished
            )
            self._transcription_worker.error.connect(
                self._on_transcription_error
            )
            self._transcription_worker.start()
        else:
            self._start_summarization(recording)

    @Slot(str)
    def _on_chain_transcription_finished(self, transcript):
        """Handle transcription in auto-chain, then summarize."""
        recording = self._get_selected_recording()
        if recording and recording.get("id"):
            try:
                self.vault_manager.update_recording(
                    recording["id"],
                    transcription=transcript,
                )
                recording["transcription"] = transcript
            except Exception as e:
                logger.error(
                    "Failed to store transcription: %s", e
                )

        self.update_status("Transcription complete. Summarizing...")
        self._start_summarization(recording)

    def _start_summarization(self, recording):
        """Start the summarization worker."""
        self._set_processing(True)
        self.update_status("Summarizing...")

        self._summarization_worker = OnDemandSummarizationWorker(
            self.summarizer_service, recording
        )
        self._summarization_worker.finished.connect(
            self._on_summarization_finished
        )
        self._summarization_worker.error.connect(
            self._on_summarization_error
        )
        self._summarization_worker.start()

    @Slot(dict)
    def _on_summarization_finished(self, result):
        """Handle successful summarization."""
        recording = self._get_selected_recording()
        summary = result.get("summary", "")
        markdown_path = result.get("markdown_path")

        if recording and recording.get("id"):
            try:
                self.vault_manager.update_recording(
                    recording["id"],
                    summary=summary,
                    markdown_path=markdown_path,
                )
                recording["summary"] = summary
                if markdown_path:
                    recording["markdown_path"] = markdown_path
            except Exception as e:
                logger.error(
                    "Failed to store summary: %s", e
                )

        self._set_processing(False)
        self.update_status("Summarization complete")
        self.show_recording_details()

        # Open SummaryViewerDialog
        if recording:
            try:
                summary_viewer = SummaryViewerDialog(
                    self,
                    vault_manager=self.vault_manager,
                    template_manager=self.template_manager,
                )
                summary_viewer.load_recording_data(
                    recording, recording.get("markdown_path")
                )
                self._current_viewer = summary_viewer
                self._current_recording = recording
                summary_viewer.regenerate_requested.connect(
                    self._handle_regeneration_request
                )
                summary_viewer.exec()
            except Exception as e:
                logger.error(
                    "Error opening summary viewer: %s", e
                )

    @Slot(str)
    def _on_summarization_error(self, error_msg):
        """Handle summarization error."""
        self._set_processing(False)
        self.update_status("Summarization failed")
        QMessageBox.critical(
            self,
            "Summarization Error",
            f"Failed to summarize recording: {error_msg}",
        )

    def delete_recording(self):
        """Delete the selected recording."""
        current_row = self.recordings_table.currentRow()
        if current_row < 0:
            QMessageBox.information(
                self, "No Selection", "Please select a recording to delete."
            )
            return

        title_item = self.recordings_table.item(current_row, 0)
        recording = title_item.data(Qt.UserRole)

        if not recording:
            QMessageBox.warning(
                self, "Error", "Could not retrieve recording data."
            )
            return

        rec_title = recording.get("title", "Untitled")
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete the"
            f" recording '{rec_title}'?\n\n"
            "This will permanently remove the"
            " recording, its audio file, "
            "transcription, and summary.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                recording_id = recording.get("id")
                if recording_id is None:
                    QMessageBox.warning(
                        self, "Delete Error", "Recording has no ID."
                    )
                    return

                # Delete associated files
                self._delete_recording_files(recording)

                # Delete database entry
                self.vault_manager.delete_recording(recording_id)

                # Refresh the vault list
                self.load_recordings()
                self.show_empty_details()
                self.update_status(f"Recording '{rec_title}' deleted")

            except VaultException as e:
                logger.error(f"Error deleting recording: {e}")
                QMessageBox.warning(
                    self, "Delete Error", f"Failed to delete recording: {e}"
                )
            except Exception as e:
                logger.error(f"Error deleting recording: {e}")
                QMessageBox.critical(
                    self, "Delete Error", f"Failed to delete recording: {e}"
                )

    def _delete_recording_files(self, recording: Dict):
        """Delete files associated with a recording."""
        vault_dir = self.vault_manager.vault_dir

        # Delete audio file
        filename = recording.get("filename")
        if filename:
            audio_path = vault_dir / filename
            if audio_path.exists():
                try:
                    audio_path.unlink()
                    logger.info(
                        "Deleted audio file: %s",
                        audio_path,
                    )
                except OSError as e:
                    logger.warning(
                        "Could not delete audio" " file %s: %s",
                        audio_path,
                        e,
                    )

        # Delete markdown summary file
        markdown_path = recording.get("markdown_path")
        if markdown_path:
            md_path = Path(markdown_path)
            if md_path.exists():
                try:
                    md_path.unlink()
                    logger.info(
                        "Deleted markdown file: %s",
                        md_path,
                    )
                except OSError as e:
                    logger.warning(
                        "Could not delete markdown" " file %s: %s",
                        md_path,
                        e,
                    )

    def export_recording(self):
        """Export selected recording files to a directory."""
        current_row = self.recordings_table.currentRow()
        if current_row < 0:
            QMessageBox.information(
                self, "No Selection", "Please select a recording to export."
            )
            return

        title_item = self.recordings_table.item(current_row, 0)
        recording = title_item.data(Qt.UserRole)

        if not recording:
            QMessageBox.warning(
                self, "Error", "Could not retrieve recording data."
            )
            return

        # Open directory picker
        export_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Export Directory",
            str(Path.home()),
        )

        if not export_dir:
            return  # User cancelled

        export_path = Path(export_dir)
        title = recording.get("title") or recording.get("filename", "Untitled")
        safe_title = sanitize_title(title)

        # Create a per-recording subfolder (with dedup)
        subfolder = create_unique_subfolder(export_path, safe_title)

        exported_files = []
        try:
            # Export audio file (renamed to title-based name)
            filename = recording.get("filename")
            if filename:
                audio_src = self.vault_manager.vault_dir / filename
                try:
                    validate_path_within(
                        audio_src, self.vault_manager.vault_dir
                    )
                except ValueError as e:
                    logger.warning(f"Export skipped: {e}")
                    audio_src = None
                if audio_src and audio_src.exists():
                    ext = Path(filename).suffix
                    audio_name = f"{safe_title}{ext}"
                    audio_dst = subfolder / audio_name
                    shutil.copy2(str(audio_src), str(audio_dst))
                    exported_files.append(audio_name)

            # Export transcription as .txt
            transcription = recording.get("transcription")
            if transcription:
                txt_name = f"{safe_title}_transcription.txt"
                txt_path = subfolder / txt_name
                txt_path.write_text(transcription, encoding="utf-8")
                exported_files.append(txt_name)

            # Export SRT subtitle file when timestamps are available
            exporter = TranscriptionExporter(recording)
            if exporter.has_timestamps():
                srt_name = f"{safe_title}.srt"
                srt_path = subfolder / srt_name
                exporter.export_srt(srt_path)
                exported_files.append(srt_name)

            # Export full details as .md
            md_name = f"{safe_title}_summary.md"
            md_path = subfolder / md_name
            rec_title = recording.get("title", "Untitled")
            lines = [f"# {rec_title}\n\n"]
            fname = recording.get("filename", "N/A")
            lines.append(f"**Filename:** {fname}\n")
            cat = recording.get("category", "other").title()
            lines.append(f"**Category:** {cat}\n")
            dur = self.format_duration(recording.get("duration", 0))
            lines.append(f"**Duration:** {dur}\n")
            fsize = self.format_file_size(recording.get("file_size", 0))
            lines.append(f"**File Size:** {fsize}\n")
            created = recording.get("created_at", "Unknown")
            lines.append(f"**Created:** {created}\n")

            if recording.get("description"):
                lines.append(
                    "\n## Description\n\n" f"{recording['description']}\n"
                )

            if recording.get("transcription"):
                lines.append(
                    "\n## Transcription\n\n" f"{recording['transcription']}\n"
                )

            if recording.get("summary"):
                lines.append("\n## AI Summary\n\n" f"{recording['summary']}\n")

            if recording.get("key_points"):
                lines.append("\n## Key Points\n\n")
                for point in recording["key_points"]:
                    lines.append(f"- {point}\n")

            if recording.get("tags"):
                tags_str = ", ".join(recording["tags"])
                lines.append(f"\n**Tags:** {tags_str}\n")

            md_path.write_text("".join(lines), encoding="utf-8")
            exported_files.append(md_name)

            if exported_files:
                files_list = "\n".join(f"  - {f}" for f in exported_files)
                QMessageBox.information(
                    self,
                    "Export Complete",
                    f"Exported {len(exported_files)}"
                    f" file(s) to:\n"
                    f"{subfolder}\n\n{files_list}",
                )
                self.update_status(
                    f"Exported {len(exported_files)}"
                    f" files to {subfolder}"
                )
            else:
                QMessageBox.information(
                    self,
                    "Export",
                    "No files were available to export" " for this recording.",
                )

        except Exception as e:
            logger.error(f"Error exporting recording: {e}")
            QMessageBox.critical(
                self, "Export Error", f"Failed to export recording: {e}"
            )

    def open_vault_folder(self):
        """Open the vault folder in file manager."""
        try:
            vault_path = self.vault_manager.vault_dir
            if not vault_path.exists():
                QMessageBox.warning(
                    self,
                    "Folder Not Found",
                    "Vault folder not found:" f" {vault_path}",
                )
                return

            import platform
            import subprocess

            system = platform.system()
            if system == "Windows":
                os.startfile(str(vault_path))
            elif system == "Darwin":  # macOS
                subprocess.run(
                    ["open", str(vault_path)],
                    check=True,
                )
            else:  # Linux and others
                subprocess.run(
                    ["xdg-open", str(vault_path)],
                    check=True,
                )

        except Exception as e:
            logger.error(f"Error opening vault folder: {e}")
            # Fallback - show path in message box
            QMessageBox.information(
                self,
                "Vault Folder",
                "Vault folder location:"
                f"\n{vault_path}"
                f"\n\nError opening folder: {e}",
            )

    def play_audio(self):
        """Play the audio file using the system player."""
        current_row = self.recordings_table.currentRow()
        if current_row < 0:
            QMessageBox.information(
                self, "No Selection", "Please select a recording to play."
            )
            return

        title_item = self.recordings_table.item(current_row, 0)
        recording = title_item.data(Qt.UserRole)
        if not recording:
            QMessageBox.warning(
                self, "Error", "Could not retrieve recording data."
            )
            return

        filename = recording.get("filename", "")
        vault_dir = self.vault_manager.vault_dir
        audio_file = vault_dir / filename
        try:
            validate_path_within(audio_file, vault_dir)
        except ValueError:
            logger.warning(f"Path traversal blocked in play_audio: {filename}")
            QMessageBox.warning(
                self, "Invalid Path", "The audio file path is invalid."
            )
            return
        if not audio_file.exists():
            QMessageBox.warning(
                self, "File Not Found", f"Audio file not found:\n{audio_file}"
            )
            return

        try:
            import platform
            import subprocess

            system = platform.system()
            if system == "Windows":
                os.startfile(str(audio_file))
            elif system == "Darwin":
                subprocess.run(["open", str(audio_file)])
            else:
                subprocess.run(["xdg-open", str(audio_file)])

            self.update_status(f"Playing {filename}")
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
            QMessageBox.warning(
                self, "Playback Error", f"Could not play audio: {e}"
            )

    def edit_recording(self):
        """Open an edit dialog for the selected recording."""
        current_row = self.recordings_table.currentRow()
        if current_row < 0:
            QMessageBox.information(
                self, "No Selection", "Please select a recording to edit."
            )
            return

        title_item = self.recordings_table.item(current_row, 0)
        recording = title_item.data(Qt.UserRole)
        if not recording:
            QMessageBox.warning(
                self, "Error", "Could not retrieve recording data."
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Recording")
        dialog.setMinimumSize(400, 300)

        layout = QVBoxLayout(dialog)

        form_layout = QGridLayout()

        form_layout.addWidget(QLabel("Title:"), 0, 0)
        title_edit = QLineEdit(recording.get("title", ""))
        form_layout.addWidget(title_edit, 0, 1)

        form_layout.addWidget(QLabel("Description:"), 1, 0, Qt.AlignTop)
        desc_edit = QTextEdit()
        desc_edit.setPlainText(recording.get("description", ""))
        desc_edit.setMaximumHeight(120)
        form_layout.addWidget(desc_edit, 1, 1)

        form_layout.addWidget(QLabel("Category:"), 2, 0)
        category_combo = QComboBox()
        category_combo.addItems(
            ["meeting", "interview", "lecture", "note",
             "call", "presentation", "uncategorized"]
        )
        current_cat = recording.get("category", "uncategorized")
        idx = category_combo.findText(current_cat)
        if idx >= 0:
            category_combo.setCurrentIndex(idx)
        form_layout.addWidget(category_combo, 2, 1)

        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(
            "QPushButton { background-color: #0078d4;" " color: white; }"
        )
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

        def save_changes():
            try:
                recording_id = recording.get("id")
                if recording_id is None:
                    QMessageBox.warning(
                        dialog, "Error", "Recording has no ID."
                    )
                    return

                self.vault_manager.update_recording(
                    recording_id,
                    title=title_edit.text().strip(),
                    description=(desc_edit.toPlainText().strip()),
                    category=(category_combo.currentText()),
                )
                new_title = title_edit.text().strip()
                self.update_status(f"Recording '{new_title}' updated")
                dialog.accept()
                self.load_recordings()
            except VaultException as e:
                logger.error(f"Error updating recording: {e}")
                QMessageBox.warning(
                    dialog,
                    "Update Error",
                    "Failed to update recording:" f" {e}",
                )

        save_btn.clicked.connect(save_changes)
        dialog.exec()

    def format_duration(self, seconds: float) -> str:
        """Format duration in seconds to MM:SS format."""
        if not seconds or seconds <= 0:
            return "0:00"

        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def format_file_size(self, bytes_size: int) -> str:
        """Format file size to human readable format."""
        if not bytes_size or bytes_size <= 0:
            return "0 B"

        for unit in ["B", "KB", "MB", "GB"]:
            if bytes_size < 1024:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.1f} TB"

    def update_count_label(self, count: int):
        """Update the recordings count label."""
        self.count_label.setText(f"Total recordings: {count}")

    def update_status(self, message: str):
        """Update the status label."""
        self.status_label.setText(message)
        QTimer.singleShot(3000, lambda: self.status_label.setText("Ready"))
