"""
Main application window for ScribeVault using PySide6.
"""

import sys
import os
import threading
from pathlib import Path
from typing import Optional
import logging
import traceback
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTextEdit, QCheckBox, QFrame, QStatusBar,
    QScrollArea, QProgressBar, QSplitter, QTabWidget, QMenuBar,
    QToolBar, QSystemTrayIcon, QApplication, QMessageBox, QDialog
)
from PySide6.QtCore import (
    Qt, QTimer, QThread, Signal, QSettings, QSize, QRect,
    QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup
)
from PySide6.QtGui import (
    QIcon, QFont, QPixmap, QAction, QPalette, QColor,
    QKeySequence, QShortcut, QPainter, QBrush
)

from audio.recorder import AudioRecorder, AudioException
from transcription.whisper_service import WhisperService, TranscriptionException
from ai.summarizer import SummarizerService
from vault.manager import VaultManager, VaultException
from config.settings import SettingsManager
from gui.qt_app import ScribeVaultWorker
from gui.qt_settings_dialog import SettingsDialog
from gui.qt_vault_dialog import VaultDialog
from gui.qt_summary_viewer import SummaryViewerDialog

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RecordingWorker(ScribeVaultWorker):
    """Worker thread for audio recording processing."""
    
    def __init__(self, audio_path: Path, services: dict):
        super().__init__()
        self.audio_path = audio_path
        self.whisper_service = services['whisper']
        self.summarizer_service = services['summarizer']
        self.vault_manager = services['vault']
        self.generate_summary = services.get('generate_summary', False)
        
    def run(self):
        """Process the recording in background thread."""
        try:
            self.emit_status("Processing audio file...")
            self.emit_progress(10)
            
            if self.is_cancelled():
                return
                
            # Transcribe audio if service is available
            transcript = None
            if self.whisper_service:
                self.emit_status("Transcribing audio...")
                self.emit_progress(30)
                
                transcript = self.whisper_service.transcribe_audio(str(self.audio_path))
            else:
                self.emit_status("Transcription service not available - skipping...")
                logger.warning("Whisper service not available - recording saved without transcription")
                
            if self.is_cancelled():
                return
                
            self.emit_progress(60)
            
            # Generate summary if requested and services are available
            summary = None
            markdown_path = None
            
            if self.generate_summary and transcript and self.summarizer_service:
                self.emit_status("Generating AI summary...")
                self.emit_progress(80)
                
                # Prepare recording data
                recording_data = {
                    'filename': self.audio_path.name,
                    'transcription': transcript,
                    'file_size': self.audio_path.stat().st_size,
                    'duration': self._get_audio_duration(),
                    'created_at': datetime.now().isoformat(),
                    'category': 'other'
                }
                
                summary_result = self.summarizer_service.generate_summary_with_markdown(recording_data)
                summary = summary_result.get('summary')
                markdown_path = summary_result.get('markdown_path')
            elif self.generate_summary and not self.summarizer_service:
                self.emit_status("AI summarization service not available - skipping...")
                logger.warning("Summarizer service not available - recording saved without summary")
                
            if self.is_cancelled():
                return
                
            # Save to vault if vault manager is available
            recording_id = None
            if self.vault_manager:
                self.emit_status("Saving to vault...")
                self.emit_progress(90)
                
                recording_id = self.vault_manager.add_recording(
                    filename=self.audio_path.name,
                    transcription=transcript,
                    summary=summary,
                    file_size=self.audio_path.stat().st_size,
                    duration=self._get_audio_duration(),
                    markdown_path=markdown_path
                )
            else:
                self.emit_status("Vault service not available - recording saved locally only")
                logger.warning("Vault manager not available - recording not saved to database")
            
            self.emit_progress(100)
            self.emit_status("Processing complete!")
            
            # Emit results
            result = {
                'transcript': transcript,
                'summary': summary,
                'markdown_path': markdown_path,
                'recording_id': recording_id
            }
            
            self.finished.emit(result)
            
        except Exception as e:
            logger.error(f"Recording processing failed: {e}")
            self.error.emit(str(e))
            
    def _get_audio_duration(self) -> float:
        """Get audio file duration."""
        try:
            import wave
            with wave.open(str(self.audio_path), 'rb') as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                return frames / float(sample_rate)
        except Exception:
            return 0.0


class AnimatedRecordButton(QPushButton):
    """Custom record button with pulsing animation."""
    
    def __init__(self, text: str = "🎙️ Start Recording", parent=None):
        super().__init__(text, parent)
        
        self.is_recording = False
        self.setup_styling()
        self.setup_animation()
        
    def setup_styling(self):
        """Setup button styling."""
        self.setMinimumSize(160, 50)
        self.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.setProperty("class", "RecordButton")
        
    def setup_animation(self):
        """Setup pulsing animation for recording state."""
        self.animation = QPropertyAnimation(self, b"opacity")
        self.animation.setDuration(1000)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.6)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Create looping animation
        self.animation_group = QSequentialAnimationGroup()
        self.animation_group.addAnimation(self.animation)
        
        # Reverse animation
        reverse_animation = QPropertyAnimation(self, b"opacity")
        reverse_animation.setDuration(1000)
        reverse_animation.setStartValue(0.6)
        reverse_animation.setEndValue(1.0)
        reverse_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        self.animation_group.addAnimation(reverse_animation)
        self.animation_group.setLoopCount(-1)  # Infinite loop
        
    def set_recording_state(self, recording: bool):
        """Set recording state and update appearance."""
        self.is_recording = recording
        
        if recording:
            self.setText("⏹️ Stop Recording")
            self.setProperty("recording", "true")
            self.animation_group.start()
        else:
            self.setText("🎙️ Start Recording")
            self.setProperty("recording", "false")
            self.animation_group.stop()
            self.setGraphicsEffect(None)  # Remove any effects
            
        # Force style update
        self.style().unpolish(self)
        self.style().polish(self)


class ScribeVaultMainWindow(QMainWindow):
    """Main application window for ScribeVault."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize services
        self.initialize_services()
        
        # Window state
        self._recording_lock = threading.Lock()
        self.is_recording = False
        self.current_recording_path: Optional[Path] = None
        self.current_worker: Optional[RecordingWorker] = None
        self.current_recording_data: Optional[dict] = None
        self.current_markdown_path: Optional[str] = None
        
        # Setup UI
        self.setup_window()
        self.setup_ui()
        self.setup_shortcuts()
        self.setup_timer()
        
        # Load settings
        self.load_settings()
        
        logger.info("ScribeVault main window initialized")
        
    def initialize_services(self):
        """Initialize all application services."""
        # Initialize settings manager first
        try:
            self.settings_manager = SettingsManager()
            logger.info("Settings manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize settings manager: {e}")
            QMessageBox.critical(
                self, 
                "Initialization Error",
                f"Failed to initialize settings manager:\n{e}"
            )
            self.settings_manager = None
        
        # Initialize audio recorder
        try:
            self.audio_recorder = AudioRecorder()
            logger.info("Audio recorder initialized")
        except Exception as e:
            logger.error(f"Failed to initialize audio recorder: {e}")
            QMessageBox.critical(
                self, 
                "Initialization Error",
                f"Failed to initialize audio recorder:\n{e}"
            )
            self.audio_recorder = None
        
        # Initialize whisper service
        try:
            self.whisper_service = WhisperService(self.settings_manager)
            logger.info("Whisper service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize whisper service: {e}")
            # Don't show critical error for whisper - just warn user
            logger.warning("Transcription service not available - recordings will be saved without transcription")
            self.whisper_service = None
        
        # Initialize summarizer service
        try:
            self.summarizer_service = SummarizerService(settings_manager=self.settings_manager)
            logger.info("Summarizer service initialized")
        except ValueError as e:
            logger.warning(f"AI summarization not available: {e}")
            self.summarizer_service = None
        except Exception as e:
            logger.error(f"Failed to initialize summarizer service: {e}")
            logger.warning("AI summarization service not available - recordings will be saved without summaries")
            self.summarizer_service = None
        
        # Initialize vault manager
        try:
            self.vault_manager = VaultManager()
            logger.info("Vault manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize vault manager: {e}")
            QMessageBox.critical(
                self, 
                "Initialization Error",
                f"Failed to initialize vault manager:\n{e}"
            )
            self.vault_manager = None
            
        logger.info("Service initialization completed")
            
    def setup_window(self):
        """Setup main window properties."""
        self.setWindowTitle("ScribeVault")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        # Center window on screen
        screen = QApplication.primaryScreen().geometry()
        window_rect = self.geometry()
        center_x = (screen.width() - window_rect.width()) // 2
        center_y = (screen.height() - window_rect.height()) // 2
        self.move(center_x, center_y)
        
        # Set window icon
        icon_path = Path("src/assets/icons/app_icon.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
            
    def setup_ui(self):
        """Setup the user interface."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        self.create_header(main_layout)
        
        # Content area
        content_splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(content_splitter, 1)
        
        # Text areas
        self.create_text_areas(content_splitter)
        
        # Controls
        self.create_controls(main_layout)
        
        # Status bar
        self.create_status_bar()
        
        # Menu bar
        self.create_menu_bar()
        
    def create_header(self, parent_layout):
        """Create the application header."""
        header_frame = QFrame()
        header_frame.setProperty("class", "HeaderFrame")
        header_frame.setFixedHeight(120)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 20, 20, 20)
        
        # Logo/Title
        title_label = QLabel("ScribeVault")
        title_label.setFont(QFont("Segoe UI", 28, QFont.Bold))
        title_label.setStyleSheet("color: white;")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Version info
        version_label = QLabel("v2.0.0")
        version_label.setFont(QFont("Segoe UI", 10))
        version_label.setStyleSheet("color: #cccccc;")
        header_layout.addWidget(version_label)
        
        parent_layout.addWidget(header_frame)
        
    def create_text_areas(self, parent_splitter):
        """Create transcription and summary text areas."""
        # Transcription area
        transcript_widget = QWidget()
        transcript_layout = QVBoxLayout(transcript_widget)
        transcript_layout.setContentsMargins(20, 10, 20, 10)
        
        transcript_label = QLabel("📝 Transcribed Text")
        transcript_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        transcript_layout.addWidget(transcript_label)
        
        self.transcript_text = QTextEdit()
        self.transcript_text.setProperty("class", "TranscriptArea")
        self.transcript_text.setPlaceholderText("Click 'Start Recording' to begin capturing audio...")
        self.transcript_text.setFont(QFont("Segoe UI", 12))
        self.transcript_text.setReadOnly(True)
        transcript_layout.addWidget(self.transcript_text)
        
        parent_splitter.addWidget(transcript_widget)
        
        # Summary area
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)
        summary_layout.setContentsMargins(20, 10, 20, 10)
        
        self.summary_label = QLabel("🤖 AI Summary")
        self.summary_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        summary_layout.addWidget(self.summary_label)
        
        self.summary_text = QTextEdit()
        self.summary_text.setProperty("class", "SummaryArea")
        self.summary_text.setPlaceholderText("AI summary will appear here when enabled...")
        self.summary_text.setFont(QFont("Segoe UI", 12))
        self.summary_text.setReadOnly(True)
        summary_layout.addWidget(self.summary_text)
        
        parent_splitter.addWidget(summary_widget)
        
        # Set initial splitter sizes (60% transcript, 40% summary)
        parent_splitter.setSizes([300, 200])
        
    def create_controls(self, parent_layout):
        """Create control panel with buttons and options."""
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(20, 20, 20, 20)
        
        # Generate Summary checkbox
        self.summary_checkbox = QCheckBox("Generate AI Summary")
        self.summary_checkbox.setFont(QFont("Segoe UI", 12))
        self.summary_checkbox.toggled.connect(self.on_summary_toggle)
        controls_layout.addWidget(self.summary_checkbox)
        
        controls_layout.addStretch()
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumWidth(200)
        controls_layout.addWidget(self.progress_bar)
        
        controls_layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # Record button
        self.record_button = AnimatedRecordButton()
        self.record_button.clicked.connect(self.toggle_recording)
        button_layout.addWidget(self.record_button)
        
        # Vault button
        self.vault_button = QPushButton("📚 Vault")
        self.vault_button.setProperty("class", "VaultButton")
        self.vault_button.setMinimumSize(100, 50)
        self.vault_button.setFont(QFont("Segoe UI", 12))
        self.vault_button.clicked.connect(self.show_vault)
        button_layout.addWidget(self.vault_button)
        
        # Settings button
        self.settings_button = QPushButton("⚙️ Settings")
        self.settings_button.setProperty("class", "SettingsButton")
        self.settings_button.setMinimumSize(100, 50)
        self.settings_button.setFont(QFont("Segoe UI", 12))
        self.settings_button.clicked.connect(self.show_settings)
        button_layout.addWidget(self.settings_button)
        
        # Markdown button (hidden by default)
        self.markdown_button = QPushButton("📄 Summary")
        self.markdown_button.setProperty("class", "MarkdownButton")
        self.markdown_button.setMinimumSize(120, 50)
        self.markdown_button.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.markdown_button.clicked.connect(self.show_markdown_summary)
        self.markdown_button.setVisible(False)
        button_layout.addWidget(self.markdown_button)
        
        controls_layout.addLayout(button_layout)
        parent_layout.addWidget(controls_frame)
        
    def create_status_bar(self):
        """Create status bar with indicators."""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # Status message
        self.status_label = QLabel("Ready")
        status_bar.addWidget(self.status_label)
        
        status_bar.addPermanentWidget(QLabel("  |  "))
        
        # Recording indicator
        self.recording_indicator = QLabel("")
        self.recording_indicator.setStyleSheet("font-weight: bold; color: #d32f2f;")
        status_bar.addPermanentWidget(self.recording_indicator)
        
        # Timer for recording duration
        self.recording_timer = QLabel("")
        self.recording_timer.setStyleSheet("font-weight: bold; color: #1f538d;")
        status_bar.addPermanentWidget(self.recording_timer)
        
    def create_menu_bar(self):
        """Create application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_recording_action = QAction("&New Recording", self)
        new_recording_action.setShortcut(QKeySequence.New)
        new_recording_action.triggered.connect(self.new_recording)
        file_menu.addAction(new_recording_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        copy_transcript_action = QAction("Copy &Transcript", self)
        copy_transcript_action.setShortcut(QKeySequence("Ctrl+T"))
        copy_transcript_action.triggered.connect(self.copy_transcript)
        edit_menu.addAction(copy_transcript_action)
        
        copy_summary_action = QAction("Copy &Summary", self)
        copy_summary_action.setShortcut(QKeySequence("Ctrl+S"))
        copy_summary_action.triggered.connect(self.copy_summary)
        edit_menu.addAction(copy_summary_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        vault_action = QAction("&Vault", self)
        vault_action.setShortcut(QKeySequence("Ctrl+V"))
        vault_action.triggered.connect(self.show_vault)
        view_menu.addAction(vault_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Global shortcuts
        record_shortcut = QShortcut(QKeySequence("Space"), self)
        record_shortcut.activated.connect(self.toggle_recording)
        
        # Escape to stop recording
        stop_shortcut = QShortcut(QKeySequence("Escape"), self)
        stop_shortcut.activated.connect(self.stop_recording_shortcut)
        
    def setup_timer(self):
        """Setup recording timer."""
        self.recording_start_time = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_recording_timer)
        
    def load_settings(self):
        """Load application settings."""
        settings = QSettings()
        
        # Window geometry
        geometry = settings.value("window/geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
        # Window state
        state = settings.value("window/state")
        if state:
            self.restoreState(state)
            
        # Summary checkbox state
        generate_summary = settings.value("recording/generate_summary", False, type=bool)
        self.summary_checkbox.setChecked(generate_summary)
        
    def save_settings(self):
        """Save application settings."""
        settings = QSettings()
        settings.setValue("window/geometry", self.saveGeometry())
        settings.setValue("window/state", self.saveState())
        settings.setValue("recording/generate_summary", self.summary_checkbox.isChecked())
        
    # Event handlers and methods will be continued in the next part...
    
    def toggle_recording(self):
        """Toggle recording state."""
        with self._recording_lock:
            recording = self.is_recording
        if not recording:
            self.start_recording()
        else:
            self.stop_recording()
            
    def start_recording(self):
        """Start audio recording."""
        try:
            self.update_status("Starting recording...")

            # Clear previous transcription and summary
            self.transcript_text.clear()
            self.summary_text.clear()
            self.markdown_button.setVisible(False)

            # Clear current recording data
            self.current_recording_data = None
            self.current_markdown_path = None

            # Start recording
            self.current_recording_path = self.audio_recorder.start_recording()
            with self._recording_lock:
                self.is_recording = True
            
            # Update UI
            self.record_button.set_recording_state(True)
            self.recording_indicator.setText("🔴 RECORDING")
            
            # Start timer
            self.recording_start_time = datetime.now()
            self.timer.start(1000)  # Update every second
            
            # Disable other buttons during recording
            self.vault_button.setEnabled(False)
            self.settings_button.setEnabled(False)
            
            self.update_status("Recording in progress...")
            logger.info("Recording started")
            
        except Exception as e:
            self.handle_error("Failed to start recording", e)
            
    def stop_recording(self):
        """Stop audio recording and process."""
        try:
            with self._recording_lock:
                if not self.is_recording:
                    return
                self.is_recording = False

            self.update_status("Stopping recording...")

            # Stop recording
            recorded_file = self.audio_recorder.stop_recording()
            
            # Update UI
            self.record_button.set_recording_state(False)
            self.recording_indicator.setText("")
            self.recording_timer.setText("")
            self.timer.stop()
            
            # Re-enable buttons
            self.vault_button.setEnabled(True)
            self.settings_button.setEnabled(True)
            
            if recorded_file and recorded_file.exists():
                self.process_recording(recorded_file)
            else:
                self.update_status("Recording failed - no file created")
                
            logger.info("Recording stopped")
            
        except Exception as e:
            self.handle_error("Failed to stop recording", e)
            
    def process_recording(self, audio_path: Path):
        """Process recorded audio file."""
        try:
            self.update_status("Processing recording...")
            
            # Show progress
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            # Create worker thread
            services = {
                'whisper': self.whisper_service,
                'summarizer': self.summarizer_service,
                'vault': self.vault_manager,
                'generate_summary': self.summary_checkbox.isChecked()
            }
            
            self.current_worker = RecordingWorker(audio_path, services)
            
            # Connect signals
            self.current_worker.finished.connect(self.on_processing_finished)
            self.current_worker.error.connect(self.on_processing_error)
            self.current_worker.progress.connect(self.progress_bar.setValue)
            self.current_worker.status.connect(self.update_status)
            
            # Start processing
            self.current_worker.start()
            
        except Exception as e:
            self.handle_error("Failed to process recording", e)
            
    def on_processing_finished(self, result: dict):
        """Handle successful processing completion."""
        try:
            # Hide progress
            self.progress_bar.setVisible(False)
            
            # Store current recording data
            self.current_recording_data = {
                'filename': self.current_recording_path.name if self.current_recording_path else 'Unknown',
                'transcription': result.get('transcript'),
                'summary': result.get('summary'),
                'created_at': datetime.now().isoformat(),
                'duration': 0,  # Will be calculated if needed
                'file_size': self.current_recording_path.stat().st_size if self.current_recording_path else 0,
                'category': 'other'
            }
            self.current_markdown_path = result.get('markdown_path')
            
            # Update text areas
            if result.get('transcript'):
                self.transcript_text.setPlainText(result['transcript'])
                
            if result.get('summary'):
                summary_text = result['summary']
                if result.get('markdown_path'):
                    summary_text += f"\n\n📄 Markdown summary saved: {Path(result['markdown_path']).name}"
                    self.markdown_button.setVisible(True)
                self.summary_text.setPlainText(summary_text)
                
            self.update_status("✅ Recording processed successfully!")
            
        except Exception as e:
            logger.error(f"Error handling processing results: {e}")
            
    def on_processing_error(self, error_message: str):
        """Handle processing error."""
        self.progress_bar.setVisible(False)
        self.handle_error("Processing failed", error_message)
        
    def update_recording_timer(self):
        """Update recording duration timer."""
        if self.recording_start_time:
            elapsed = datetime.now() - self.recording_start_time
            seconds = int(elapsed.total_seconds())
            minutes = seconds // 60
            seconds = seconds % 60
            self.recording_timer.setText(f"⏱️ {minutes:02d}:{seconds:02d}")
            
    def stop_recording_shortcut(self):
        """Stop recording via keyboard shortcut."""
        if self.is_recording:
            self.stop_recording()
            
    def update_status(self, message: str):
        """Update status bar message."""
        self.status_label.setText(message)
        logger.info(f"Status: {message}")
        
    def handle_error(self, title: str, error):
        """Handle and display error messages."""
        error_msg = str(error)
        logger.error(f"{title}: {error_msg}")
        
        QMessageBox.critical(self, title, error_msg)
        self.update_status(f"❌ {title}")
        
    # Placeholder methods for UI actions
    def new_recording(self):
        """Start a new recording."""
        if not self.is_recording:
            self.transcript_text.clear()
            self.summary_text.clear()
            self.markdown_button.setVisible(False)
            
            # Clear current recording data
            self.current_recording_data = None
            self.current_markdown_path = None
            
            self.start_recording()
            
    def copy_transcript(self):
        """Copy transcript to clipboard."""
        text = self.transcript_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.update_status("Transcript copied to clipboard")
            
    def copy_summary(self):
        """Copy summary to clipboard."""
        text = self.summary_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.update_status("Summary copied to clipboard")
            
    def show_vault(self):
        """Show vault window."""
        try:
            if not self.vault_manager:
                QMessageBox.warning(
                    self,
                    "Vault Unavailable",
                    "Vault manager is not available. Please restart the application."
                )
                return
                
            vault_dialog = VaultDialog(self.vault_manager, self)
            vault_dialog.exec()
            
        except Exception as e:
            logger.error(f"Error showing vault: {e}")
            QMessageBox.critical(self, "Vault Error", f"Failed to open vault: {e}")
        
    def show_settings(self):
        """Show settings dialog."""
        try:
            if not self.settings_manager:
                QMessageBox.warning(
                    self,
                    "Settings Unavailable",
                    "Settings manager is not available. Please restart the application."
                )
                return
                
            settings_dialog = SettingsDialog(self.settings_manager, self)
            if settings_dialog.exec() == QDialog.Accepted:
                # Settings were saved, you might want to reload services here
                self.update_status("Settings updated - restart recommended for all changes to take effect")
                
        except Exception as e:
            logger.error(f"Error showing settings: {e}")
            QMessageBox.critical(self, "Settings Error", f"Failed to open settings: {e}")
        
    def show_markdown_summary(self):
        """Show AI summary viewer window."""
        try:
            if not self.current_recording_data:
                QMessageBox.information(
                    self,
                    "No Summary Available",
                    "No recording data available. Please record and process audio first."
                )
                return
                
            # Check if there's actually a summary to show
            if not self.current_recording_data.get('summary') and not self.current_markdown_path:
                QMessageBox.information(
                    self,
                    "No Summary Available",
                    "No AI summary or markdown file available for the current recording."
                )
                return
                
            # Create and show summary viewer
            summary_viewer = SummaryViewerDialog(self)
            summary_viewer.load_recording_data(self.current_recording_data, self.current_markdown_path)
            summary_viewer.exec()
            
        except Exception as e:
            logger.error(f"Error showing summary viewer: {e}")
            QMessageBox.critical(self, "Summary Viewer Error", f"Failed to open summary viewer: {e}")
        
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About ScribeVault",
            """
            <h3>ScribeVault v2.0.0</h3>
            <p>Professional Audio Transcription & AI Summary Tool</p>
            <p>Built with PySide6 for enhanced performance and native appearance.</p>
            <p>© 2025 Beekeeper Lab</p>
            """
        )
        
    def on_summary_toggle(self, checked: bool):
        """Handle summary checkbox toggle."""
        if checked:
            self.summary_text.setStyleSheet("")
            self.summary_label.setStyleSheet("")
        else:
            self.summary_text.setStyleSheet("color: #666666;")
            self.summary_label.setStyleSheet("color: #666666;")
            
    def closeEvent(self, event):
        """Handle window close event."""
        try:
            # Save settings
            self.save_settings()
            
            # Stop any ongoing recording
            with self._recording_lock:
                was_recording = self.is_recording
            if was_recording:
                self.stop_recording()
                
            # Cancel any running worker
            if self.current_worker and self.current_worker.isRunning():
                self.current_worker.cancel()
                self.current_worker.wait(3000)  # Wait up to 3 seconds
                
            # Cleanup services
            if hasattr(self, 'audio_recorder'):
                self.audio_recorder.cleanup()
                
            event.accept()
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            event.accept()  # Accept anyway to prevent hang
