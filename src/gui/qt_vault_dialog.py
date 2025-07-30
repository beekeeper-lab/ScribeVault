"""
Vault dialog for ScribeVault PySide6 application.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QWidget,
    QLabel, QPushButton, QLineEdit, QComboBox, QTextEdit, 
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
    QGroupBox, QMessageBox, QFileDialog, QProgressBar,
    QCheckBox, QSpinBox, QTabWidget, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSize
from PySide6.QtGui import QFont, QIcon, QPalette, QColor

from vault.manager import VaultManager, VaultException
from gui.qt_summary_viewer import SummaryViewerDialog
import logging

logger = logging.getLogger(__name__)


class VaultDialog(QDialog):
    """Vault dialog for managing recordings."""
    
    def __init__(self, vault_manager: VaultManager, parent=None):
        super().__init__(parent)
        self.vault_manager = vault_manager
        self.current_recordings = []
        
        self.setup_ui()
        self.show_empty_details()  # Initialize with empty state
        self.load_recordings()
        
    def setup_ui(self):
        """Setup the vault dialog UI."""
        self.setWindowTitle("ScribeVault - Recordings Vault")
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
        self.category_filter.addItems(["All", "meeting", "interview", "lecture", "note", "other"])
        self.category_filter.setMaximumWidth(120)
        self.category_filter.currentTextChanged.connect(self.filter_recordings)
        header_layout.addWidget(QLabel("Category:"))
        header_layout.addWidget(self.category_filter)
        
        refresh_button = QPushButton("🔄")
        refresh_button.setToolTip("Refresh recordings list")
        refresh_button.setMaximumWidth(35)
        refresh_button.clicked.connect(self.load_recordings)
        header_layout.addWidget(refresh_button)
        
        # Close button in header
        close_button = QPushButton("✕")
        close_button.setToolTip("Close vault")
        close_button.clicked.connect(self.accept)
        close_button.setMaximumWidth(30)
        close_button.setStyleSheet("QPushButton { background-color: #666; color: white; border-radius: 15px; }")
        header_layout.addWidget(close_button)
        
        layout.addLayout(header_layout)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - recordings table
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Recordings count (more compact)
        self.count_label = QLabel("Total recordings: 0")
        self.count_label.setStyleSheet("color: #888; font-size: 11px; padding: 3px;")
        left_layout.addWidget(self.count_label)
        
        # Recordings table
        self.recordings_table = QTableWidget()
        self.setup_table()
        left_layout.addWidget(self.recordings_table)
        
        # Compact table controls
        table_controls = QHBoxLayout()
        table_controls.setContentsMargins(0, 5, 0, 5)
        
        view_summary_button = QPushButton("🤖 View Summary")
        view_summary_button.setToolTip("View AI summary for selected recording")
        view_summary_button.clicked.connect(self.view_summary)
        view_summary_button.setStyleSheet("QPushButton { background-color: #0078d4; color: white; }")
        view_summary_button.setMaximumHeight(30)
        table_controls.addWidget(view_summary_button)
        
        delete_button = QPushButton("🗑️ Delete")
        delete_button.setToolTip("Delete selected recording")
        delete_button.clicked.connect(self.delete_recording)
        delete_button.setStyleSheet("QPushButton { background-color: #d32f2f; color: white; }")
        delete_button.setMaximumHeight(30)
        table_controls.addWidget(delete_button)
        
        export_button = QPushButton("📤 Export")
        export_button.setToolTip("Export selected recording")
        export_button.clicked.connect(self.export_recording)
        export_button.setMaximumHeight(30)
        table_controls.addWidget(export_button)
        
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
        details_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
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
        
        # Set splitter proportions (75% table area, 25% details area)
        splitter.setSizes([750, 350])
        layout.addWidget(splitter)
        
        # Small status bar at bottom
        status_frame = QFrame()
        status_frame.setMaximumHeight(30)
        status_frame.setStyleSheet("background-color: #2b2b2b; border-top: 1px solid #555;")
        
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
        headers = ["Title", "Category", "Duration", "Created", "Size"]
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
        header.resizeSection(2, 80)   # Duration
        header.resizeSection(3, 150)  # Created
        header.resizeSection(4, 80)   # Size
        
        # Connect selection change
        self.recordings_table.itemSelectionChanged.connect(self.show_recording_details)
        logger.info("Connected table selection change to show_recording_details")
        
    def load_recordings(self):
        """Load recordings from the vault."""
        try:
            self.current_recordings = self.vault_manager.get_recordings()
            self.populate_table(self.current_recordings)
            self.update_count_label(len(self.current_recordings))
            self.update_status(f"Loaded {len(self.current_recordings)} recordings")
            
        except VaultException as e:
            logger.error(f"Error loading recordings: {e}")
            QMessageBox.warning(self, "Vault Error", f"Failed to load recordings: {e}")
            self.update_status("Error loading recordings")
            
    def populate_table(self, recordings: List[Dict]):
        """Populate the table with recordings."""
        self.recordings_table.setRowCount(len(recordings))
        
        for row, recording in enumerate(recordings):
            # Title
            title = recording.get('title', 'Untitled')
            if not title:
                title = recording.get('filename', 'Unknown')
            self.recordings_table.setItem(row, 0, QTableWidgetItem(title))
            
            # Category
            category = recording.get('category', 'other')
            self.recordings_table.setItem(row, 1, QTableWidgetItem(category.title()))
            
            # Duration
            duration = recording.get('duration', 0)
            duration_str = self.format_duration(duration)
            self.recordings_table.setItem(row, 2, QTableWidgetItem(duration_str))
            
            # Created date
            created_at = recording.get('created_at', '')
            if created_at:
                try:
                    # Parse and format datetime
                    if isinstance(created_at, str):
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    else:
                        dt = created_at
                    created_str = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    created_str = str(created_at)
            else:
                created_str = "Unknown"
            self.recordings_table.setItem(row, 3, QTableWidgetItem(created_str))
            
            # File size
            file_size = recording.get('file_size', 0)
            size_str = self.format_file_size(file_size)
            self.recordings_table.setItem(row, 4, QTableWidgetItem(size_str))
            
            # Store recording data in first item for easy access
            title_item = self.recordings_table.item(row, 0)
            title_item.setData(Qt.UserRole, recording)
            logger.debug(f"Stored recording data for row {row}: {recording.get('filename', 'Unknown')}")
            
    def filter_recordings(self):
        """Filter recordings based on search and category."""
        search_text = self.search_input.text().lower()
        category_filter = self.category_filter.currentText()
        
        filtered_recordings = []
        
        for recording in self.current_recordings:
            # Check category filter
            if category_filter != "All":
                if recording.get('category', 'other') != category_filter:
                    continue
            
            # Check search text
            if search_text:
                searchable_text = " ".join([
                    recording.get('title', ''),
                    recording.get('description', ''),
                    recording.get('filename', ''),
                    recording.get('transcription', '')
                ]).lower()
                
                if search_text not in searchable_text:
                    continue
            
            filtered_recordings.append(recording)
        
        self.populate_table(filtered_recordings)
        self.update_count_label(len(filtered_recordings))
        
        # Show empty details if no recordings match the filter
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
            self.show_empty_details()
            return
            
        # Get recording data
        title_item = self.recordings_table.item(current_row, 0)
        if not title_item:
            logger.debug("No title item found, showing empty state")
            self.show_empty_details()
            return
            
        recording = title_item.data(Qt.UserRole)
        if not recording:
            logger.debug("No recording data found, showing empty state")
            self.show_empty_details()
            return
            
        logger.info(f"Showing details for recording: {recording.get('filename', 'Unknown')}")
        
        # Create details widgets
        self.create_detail_section("📝 Basic Information", [
            ("Title", recording.get('title', 'Untitled')),
            ("Filename", recording.get('filename', 'Unknown')),
            ("Category", recording.get('category', 'other').title()),
            ("Duration", self.format_duration(recording.get('duration', 0))),
            ("File Size", self.format_file_size(recording.get('file_size', 0))),
            ("Created", recording.get('created_at', 'Unknown'))
        ])
        
        if recording.get('description'):
            self.create_text_section("📋 Description", recording['description'])
        
        if recording.get('transcription'):
            self.create_text_section("🎤 Transcription", recording['transcription'])
        
        if recording.get('summary'):
            self.create_text_section("🤖 AI Summary", recording['summary'])
        
        if recording.get('key_points'):
            key_points_text = "\n".join([f"• {point}" for point in recording['key_points']])
            self.create_text_section("🔑 Key Points", key_points_text)
        
        if recording.get('tags'):
            tags_text = ", ".join(recording['tags'])
            self.create_detail_section("🏷️ Tags", [("Tags", tags_text)])
        
        self.details_layout.addStretch()
        
    def show_empty_details(self):
        """Show empty state when no recording is selected."""
        no_selection_label = QLabel("Select a recording to view details")
        no_selection_label.setAlignment(Qt.AlignCenter)
        no_selection_label.setStyleSheet("color: #888; font-style: italic; padding: 20px;")
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
        text_edit.setStyleSheet("background-color: #2b2b2b; border: 1px solid #555;")
        
        layout.addWidget(text_edit)
        self.details_layout.addWidget(group)
        
    def view_summary(self):
        """View AI summary for the selected recording."""
        current_row = self.recordings_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "No Selection", "Please select a recording to view its summary.")
            return
            
        title_item = self.recordings_table.item(current_row, 0)
        recording = title_item.data(Qt.UserRole)
        
        if not recording:
            QMessageBox.warning(self, "Error", "Could not retrieve recording data.")
            return
            
        # Check if there's a summary or markdown to show
        if not recording.get('summary') and not recording.get('markdown_path'):
            QMessageBox.information(
                self, 
                "No Summary Available", 
                f"No AI summary or markdown file available for recording '{recording.get('title', 'Untitled')}'."
            )
            return
            
        try:
            # Create and show summary viewer
            summary_viewer = SummaryViewerDialog(self)
            summary_viewer.load_recording_data(recording, recording.get('markdown_path'))
            summary_viewer.exec()
            
        except Exception as e:
            logger.error(f"Error showing summary viewer: {e}")
            QMessageBox.critical(self, "Summary Viewer Error", f"Failed to open summary viewer: {e}")
        
    def delete_recording(self):
        """Delete the selected recording."""
        current_row = self.recordings_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "No Selection", "Please select a recording to delete.")
            return
            
        title_item = self.recordings_table.item(current_row, 0)
        recording = title_item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete the recording '{recording.get('title', 'Untitled')}'?\n\n"
            "This will remove it from the vault database but not delete the audio file.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # TODO: Implement delete_recording method in VaultManager
                QMessageBox.information(self, "Delete", "Delete functionality coming soon!")
                self.update_status("Delete functionality not yet implemented")
            except Exception as e:
                logger.error(f"Error deleting recording: {e}")
                QMessageBox.warning(self, "Delete Error", f"Failed to delete recording: {e}")
                
    def export_recording(self):
        """Export the selected recording."""
        current_row = self.recordings_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "No Selection", "Please select a recording to export.")
            return
            
        # TODO: Implement export functionality
        QMessageBox.information(self, "Export", "Export functionality coming soon!")
        self.update_status("Export functionality not yet implemented")
        
    def open_vault_folder(self):
        """Open the vault folder in file manager."""
        try:
            vault_path = self.vault_manager.vault_dir
            if not vault_path.exists():
                QMessageBox.warning(self, "Folder Not Found", f"Vault folder not found: {vault_path}")
                return
                
            import platform
            import subprocess
            
            system = platform.system()
            if system == "Windows":
                os.startfile(str(vault_path))
            elif system == "Darwin":  # macOS
                subprocess.run(['open', str(vault_path)], check=True)
            else:  # Linux and others
                subprocess.run(['xdg-open', str(vault_path)], check=True)
                
        except Exception as e:
            logger.error(f"Error opening vault folder: {e}")
            # Fallback - show path in message box
            QMessageBox.information(
                self, 
                "Vault Folder", 
                f"Vault folder location:\n{vault_path}\n\nError opening folder: {e}"
            )
        
    def format_duration(self, seconds: float) -> str:
        """Format duration in seconds to MM:SS format."""
        if not seconds or seconds <= 0:
            return "0:00"
        
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"
        
    def format_file_size(self, bytes_size: int) -> str:
        """Format file size in bytes to human readable format."""
        if not bytes_size or bytes_size <= 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
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
