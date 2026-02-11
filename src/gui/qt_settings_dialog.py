"""
Settings dialog for ScribeVault PySide6 application.
"""

import os
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QWidget,
    QLabel, QPushButton, QLineEdit, QComboBox, QSpinBox, QCheckBox,
    QGroupBox, QTextEdit, QMessageBox, QFileDialog, QProgressBar,
    QSlider, QDoubleSpinBox, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QIcon

from config.settings import SettingsManager, TranscriptionSettings, SummarizationSettings, DiarizationSettings, UISettings, AudioSettings, AppSettings, AUDIO_PRESETS
import logging

logger = logging.getLogger(__name__)


class APIKeyValidator(QThread):
    """Background thread to validate API keys with live API check."""

    validation_complete = Signal(bool, str)  # success, message

    def __init__(self, settings_manager: SettingsManager, api_key: str):
        super().__init__()
        self.settings_manager = settings_manager
        self.api_key = api_key

    def run(self):
        """Validate the API key with a live API call in background."""
        try:
            is_valid, message = self.settings_manager.validate_openai_api_key_live(self.api_key)
            self.validation_complete.emit(is_valid, message)
        except Exception as e:
            self.validation_complete.emit(False, f"Validation error: {str(e)}")


class SettingsDialog(QDialog):
    """Settings dialog for ScribeVault configuration."""
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.settings = settings_manager.settings
        self.validator_thread = None
        
        self.setup_ui()
        self.load_current_settings()
        
    def setup_ui(self):
        """Setup the settings dialog UI."""
        self.setWindowTitle("ScribeVault Settings")
        self.setMinimumSize(600, 500)
        self.resize(700, 600)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_audio_tab()
        self.create_transcription_tab()
        self.create_summarization_tab()
        self.create_ui_tab()
        self.create_storage_tab()
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.test_button = QPushButton("Test Settings")
        self.test_button.clicked.connect(self.test_settings)
        button_layout.addWidget(self.test_button)
        
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        self.save_button.setDefault(True)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        
    def create_audio_tab(self):
        """Create audio recording quality settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Quality preset
        preset_group = QGroupBox("Recording Quality")
        preset_layout = QGridLayout(preset_group)

        preset_layout.addWidget(QLabel("Preset:"), 0, 0)
        self.audio_preset = QComboBox()
        for key, info in AUDIO_PRESETS.items():
            self.audio_preset.addItem(info["label"], key)
        self.audio_preset.currentIndexChanged.connect(
            self._on_audio_preset_changed
        )
        preset_layout.addWidget(self.audio_preset, 0, 1)

        self.preset_description = QLabel("")
        self.preset_description.setStyleSheet(
            "color: #888; font-size: 11px;"
        )
        self.preset_description.setWordWrap(True)
        preset_layout.addWidget(self.preset_description, 1, 0, 1, 2)

        # File-size estimate
        self.file_size_label = QLabel("")
        self.file_size_label.setStyleSheet(
            "font-weight: bold; font-size: 12px; padding: 4px;"
        )
        preset_layout.addWidget(self.file_size_label, 2, 0, 1, 2)

        layout.addWidget(preset_group)

        # Input device selection
        device_group = QGroupBox("Input Device")
        device_layout = QGridLayout(device_group)

        device_layout.addWidget(QLabel("Microphone:"), 0, 0)
        self.audio_device = QComboBox()
        self.audio_device.addItem("System Default", None)
        device_layout.addWidget(self.audio_device, 0, 1)

        self.refresh_devices_button = QPushButton("Refresh")
        self.refresh_devices_button.clicked.connect(
            self._refresh_audio_devices
        )
        device_layout.addWidget(self.refresh_devices_button, 0, 2)

        layout.addWidget(device_group)
        layout.addStretch()

        self.tab_widget.addTab(tab, "Audio")

        # Populate devices on next event-loop tick
        QTimer.singleShot(100, self._refresh_audio_devices)

    def _on_audio_preset_changed(self, index: int):
        """Handle audio preset selection change."""
        preset_key = self.audio_preset.currentData()
        if preset_key and preset_key in AUDIO_PRESETS:
            info = AUDIO_PRESETS[preset_key]
            self.preset_description.setText(
                f"{info['description']}\n"
                f"Sample rate: {info['sample_rate']} Hz  |  "
                f"Channels: {info['channels']}"
            )
            size_mb = AudioSettings.estimate_file_size_per_minute(
                info["sample_rate"], info["channels"]
            )
            self.file_size_label.setText(
                f"Estimated file size: {size_mb:.1f} MB per minute"
            )

    def _refresh_audio_devices(self):
        """Refresh the list of available audio input devices."""
        self.audio_device.clear()
        self.audio_device.addItem("System Default", None)
        try:
            import pyaudio
            pa = pyaudio.PyAudio()
            for i in range(pa.get_device_count()):
                try:
                    dev = pa.get_device_info_by_index(i)
                    if dev["maxInputChannels"] > 0:
                        self.audio_device.addItem(dev["name"], i)
                except Exception:
                    pass
            pa.terminate()
        except Exception as e:
            logger.warning(f"Could not enumerate audio devices: {e}")

    def create_transcription_tab(self):
        """Create transcription settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Service selection
        service_group = QGroupBox("Transcription Service")
        service_layout = QGridLayout(service_group)
        
        service_layout.addWidget(QLabel("Service:"), 0, 0)
        self.transcription_service = QComboBox()
        self.transcription_service.addItems(["local", "openai"])
        self.transcription_service.currentTextChanged.connect(self.on_transcription_service_changed)
        service_layout.addWidget(self.transcription_service, 0, 1)
        
        # OpenAI settings
        self.openai_group = QGroupBox("OpenAI Settings")
        openai_layout = QGridLayout(self.openai_group)
        
        openai_layout.addWidget(QLabel("API Key:"), 0, 0)
        self.openai_api_key = QLineEdit()
        self.openai_api_key.setEchoMode(QLineEdit.Password)
        self.openai_api_key.setPlaceholderText("Enter your OpenAI API key...")
        openai_layout.addWidget(self.openai_api_key, 0, 1)
        
        self.validate_key_button = QPushButton("Validate")
        self.validate_key_button.clicked.connect(self.validate_api_key)
        openai_layout.addWidget(self.validate_key_button, 0, 2)

        # API key status indicator
        self.api_key_status_label = QLabel("")
        self.api_key_status_label.setWordWrap(True)
        openai_layout.addWidget(self.api_key_status_label, 1, 0, 1, 3)

        openai_layout.addWidget(QLabel("Model:"), 2, 0)
        self.openai_model = QComboBox()
        self.openai_model.addItems(["whisper-1"])
        openai_layout.addWidget(self.openai_model, 2, 1)
        
        # Local Whisper settings
        self.local_group = QGroupBox("Local Whisper Settings")
        local_layout = QGridLayout(self.local_group)
        
        local_layout.addWidget(QLabel("Model Size:"), 0, 0)
        self.local_model = QComboBox()
        self.local_model.addItems(["tiny", "base", "small", "medium", "large"])
        local_layout.addWidget(self.local_model, 0, 1)
        
        # Model info
        model_info = QLabel(
            "• tiny: ~39 MB, fastest, least accurate\n"
            "• base: ~74 MB, good balance (recommended)\n"
            "• small: ~244 MB, better accuracy\n"
            "• medium: ~769 MB, high accuracy\n"
            "• large: ~1550 MB, highest accuracy"
        )
        model_info.setStyleSheet("color: #666; font-size: 10px;")
        model_info.setWordWrap(True)
        local_layout.addWidget(model_info, 1, 0, 1, 2)
        
        local_layout.addWidget(QLabel("Device:"), 2, 0)
        self.device = QComboBox()
        self.device.addItems(["auto", "cpu", "cuda"])
        local_layout.addWidget(self.device, 2, 1)
        
        # Common settings
        common_group = QGroupBox("Common Settings")
        common_layout = QGridLayout(common_group)
        
        common_layout.addWidget(QLabel("Language:"), 0, 0)
        self.language = QComboBox()
        self.language.addItems([
            "auto", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"
        ])
        common_layout.addWidget(self.language, 0, 1)
        
        # Speaker diarization settings
        diarization_group = QGroupBox("Speaker Diarization")
        diarization_layout = QGridLayout(diarization_group)

        self.diarization_enabled = QCheckBox("Enable speaker diarization")
        self.diarization_enabled.setToolTip(
            "Automatically identify and label different speakers in the recording"
        )
        self.diarization_enabled.toggled.connect(self._on_diarization_toggled)
        diarization_layout.addWidget(self.diarization_enabled, 0, 0, 1, 2)

        diarization_layout.addWidget(QLabel("Speaker count:"), 1, 0)
        self.diarization_speaker_count = QSpinBox()
        self.diarization_speaker_count.setRange(0, 6)
        self.diarization_speaker_count.setSpecialValueText("Auto-detect")
        self.diarization_speaker_count.setMinimum(0)
        self.diarization_speaker_count.setToolTip(
            "0 = auto-detect number of speakers, or specify 2-6"
        )
        diarization_layout.addWidget(self.diarization_speaker_count, 1, 1)

        # Wrap value so that spinning up from 0 jumps to 2
        self.diarization_speaker_count.valueChanged.connect(
            self._on_speaker_count_changed
        )

        diarization_layout.addWidget(QLabel("Sensitivity:"), 2, 0)
        sensitivity_widget = QWidget()
        sensitivity_layout = QHBoxLayout(sensitivity_widget)
        sensitivity_layout.setContentsMargins(0, 0, 0, 0)

        self.diarization_sensitivity = QSlider(Qt.Horizontal)
        self.diarization_sensitivity.setRange(0, 100)
        self.diarization_sensitivity.setValue(50)
        self.diarization_sensitivity.setTickPosition(QSlider.TicksBelow)
        self.diarization_sensitivity.setTickInterval(25)
        self.diarization_sensitivity.setToolTip(
            "How aggressively to split speakers. "
            "Lower = fewer splits, higher = more splits"
        )
        self.diarization_sensitivity.valueChanged.connect(
            self._on_sensitivity_changed
        )
        sensitivity_layout.addWidget(self.diarization_sensitivity)

        self.sensitivity_value_label = QLabel("0.50")
        self.sensitivity_value_label.setMinimumWidth(32)
        sensitivity_layout.addWidget(self.sensitivity_value_label)

        diarization_layout.addWidget(sensitivity_widget, 2, 1)

        sensitivity_hint = QLabel("Less splitting ← → More splitting")
        sensitivity_hint.setStyleSheet("color: #888; font-size: 10px;")
        sensitivity_hint.setAlignment(Qt.AlignCenter)
        diarization_layout.addWidget(sensitivity_hint, 3, 1)

        # Store references for enable/disable toggling
        self._diarization_sub_controls = [
            self.diarization_speaker_count,
            self.diarization_sensitivity,
        ]

        # Cost estimation for transcription
        cost_group = QGroupBox("Transcription Cost")
        cost_layout = QVBoxLayout(cost_group)

        self.transcription_cost_label = QLabel()
        self.transcription_cost_label.setStyleSheet("font-family: 'Courier New', monospace; font-size: 12px;")
        cost_layout.addWidget(self.transcription_cost_label)

        cost_info = QLabel(
            "OpenAI charges $0.006 per minute ($0.36/hour). "
            "Local Whisper is free but uses your computer's resources."
        )
        cost_info.setStyleSheet("color: #888; font-size: 10px; font-style: italic;")
        cost_info.setWordWrap(True)
        cost_layout.addWidget(cost_info)

        # Add groups to layout
        layout.addWidget(service_group)
        layout.addWidget(self.openai_group)
        layout.addWidget(self.local_group)
        layout.addWidget(common_group)
        layout.addWidget(diarization_group)
        layout.addWidget(cost_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "🎤 Transcription")
        
    def create_summarization_tab(self):
        """Create summarization settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Enable/disable
        self.summarization_enabled = QCheckBox("Enable AI Summarization")
        self.summarization_enabled.toggled.connect(self.on_summarization_toggled)
        layout.addWidget(self.summarization_enabled)
        
        # Settings group
        self.summary_group = QGroupBox("Summarization Settings")
        summary_layout = QGridLayout(self.summary_group)
        
        summary_layout.addWidget(QLabel("Service:"), 0, 0)
        self.summary_service = QComboBox()
        self.summary_service.addItems(["openai"])
        summary_layout.addWidget(self.summary_service, 0, 1)
        
        summary_layout.addWidget(QLabel("Model:"), 1, 0)
        self.summary_model = QComboBox()
        self.summary_model.addItems([
            "gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"
        ])
        self.summary_model.currentTextChanged.connect(self.update_cost_estimation)
        summary_layout.addWidget(self.summary_model, 1, 1)
        
        summary_layout.addWidget(QLabel("Style:"), 2, 0)
        self.summary_style = QComboBox()
        self.summary_style.addItems(["concise", "detailed", "bullet_points"])
        summary_layout.addWidget(self.summary_style, 2, 1)
        
        summary_layout.addWidget(QLabel("Max Tokens:"), 3, 0)
        self.max_tokens = QSpinBox()
        self.max_tokens.setRange(100, 4000)
        self.max_tokens.setValue(500)
        self.max_tokens.valueChanged.connect(self.update_cost_estimation)
        summary_layout.addWidget(self.max_tokens, 3, 1)
        
        # Cost estimation
        cost_group = QGroupBox("💰 Cost Estimation")
        cost_layout = QVBoxLayout(cost_group)
        
        # Cost breakdown
        self.cost_breakdown = QLabel()
        self.cost_breakdown.setStyleSheet("font-family: 'Courier New', monospace; font-size: 11px;")
        cost_layout.addWidget(self.cost_breakdown)
        
        # Total cost highlight
        self.cost_total = QLabel("Total estimated cost per hour: $0.00")
        self.cost_total.setStyleSheet(
            "font-weight: bold; font-size: 14px; color: #2196F3; "
            "padding: 8px; background-color: #1e1e1e; border-radius: 4px; margin: 4px;"
        )
        self.cost_total.setAlignment(Qt.AlignCenter)
        cost_layout.addWidget(self.cost_total)
        
        # Duration selector for estimation
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Estimate for:"))
        
        self.duration_spinbox = QDoubleSpinBox()
        self.duration_spinbox.setRange(0.1, 24.0)
        self.duration_spinbox.setValue(1.0)
        self.duration_spinbox.setSuffix(" hours")
        self.duration_spinbox.setDecimals(1)
        self.duration_spinbox.valueChanged.connect(self.update_cost_estimation)
        duration_layout.addWidget(self.duration_spinbox)
        
        duration_layout.addStretch()
        cost_layout.addLayout(duration_layout)
        
        # Service comparison button
        self.compare_button = QPushButton("📊 Compare Services")
        self.compare_button.clicked.connect(self.show_service_comparison)
        cost_layout.addWidget(self.compare_button)
        
        cost_info = QLabel(
            "💡 Costs are estimated based on current OpenAI pricing. "
            "Local Whisper transcription is free but requires computational resources. "
            "Actual costs may vary depending on audio quality and content length."
        )
        cost_info.setStyleSheet("color: #888; font-size: 10px; font-style: italic;")
        cost_info.setWordWrap(True)
        cost_layout.addWidget(cost_info)
        
        layout.addWidget(self.summary_group)
        layout.addWidget(cost_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "🤖 AI Summary")
        
    def create_ui_tab(self):
        """Create UI settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Theme settings
        theme_group = QGroupBox("Appearance")
        theme_layout = QGridLayout(theme_group)
        
        theme_layout.addWidget(QLabel("Theme:"), 0, 0)
        self.theme = QComboBox()
        self.theme.addItems(["dark", "light", "system"])
        theme_layout.addWidget(self.theme, 0, 1)
        
        # Window settings
        window_group = QGroupBox("Window")
        window_layout = QGridLayout(window_group)
        
        window_layout.addWidget(QLabel("Default Width:"), 0, 0)
        self.window_width = QSpinBox()
        self.window_width.setRange(800, 3840)
        self.window_width.setValue(1200)
        window_layout.addWidget(self.window_width, 0, 1)
        
        window_layout.addWidget(QLabel("Default Height:"), 1, 0)
        self.window_height = QSpinBox()
        self.window_height.setRange(600, 2160)
        self.window_height.setValue(800)
        window_layout.addWidget(self.window_height, 1, 1)
        
        # Other settings
        other_group = QGroupBox("Behavior")
        other_layout = QVBoxLayout(other_group)
        
        self.auto_save = QCheckBox("Auto-save recordings to vault")
        other_layout.addWidget(self.auto_save)
        
        layout.addWidget(theme_group)
        layout.addWidget(window_group)
        layout.addWidget(other_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "🎨 Interface")
        
    def create_storage_tab(self):
        """Create storage settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Directories
        dirs_group = QGroupBox("Storage Directories")
        dirs_layout = QGridLayout(dirs_group)
        
        dirs_layout.addWidget(QLabel("Recordings:"), 0, 0)
        self.recordings_dir = QLineEdit()
        dirs_layout.addWidget(self.recordings_dir, 0, 1)
        
        browse_recordings = QPushButton("Browse...")
        browse_recordings.clicked.connect(self.browse_recordings_dir)
        dirs_layout.addWidget(browse_recordings, 0, 2)
        
        dirs_layout.addWidget(QLabel("Vault:"), 1, 0)
        self.vault_dir = QLineEdit()
        dirs_layout.addWidget(self.vault_dir, 1, 1)
        
        browse_vault = QPushButton("Browse...")
        browse_vault.clicked.connect(self.browse_vault_dir)
        dirs_layout.addWidget(browse_vault, 1, 2)
        
        # Info
        info_group = QGroupBox("Storage Information")
        info_layout = QVBoxLayout(info_group)
        
        self.storage_info = QLabel("Loading storage information...")
        info_layout.addWidget(self.storage_info)
        
        layout.addWidget(dirs_group)
        layout.addWidget(info_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "💾 Storage")
        
        # Update storage info
        QTimer.singleShot(100, self.update_storage_info)
        
    def on_transcription_service_changed(self, service: str):
        """Handle transcription service change."""
        self.openai_group.setVisible(service == "openai")
        self.local_group.setVisible(service == "local")
        self.update_cost_estimation()
        self.update_transcription_cost()

    def _on_diarization_toggled(self, enabled: bool):
        """Enable or disable diarization sub-controls based on checkbox."""
        for ctrl in self._diarization_sub_controls:
            ctrl.setEnabled(enabled)

    def _on_speaker_count_changed(self, value: int):
        """Ensure speaker count skips 1 (invalid — must be 0 or 2-6)."""
        if value == 1:
            self.diarization_speaker_count.setValue(2)

    def _on_sensitivity_changed(self, value: int):
        """Update the sensitivity value label when the slider moves."""
        self.sensitivity_value_label.setText(f"{value / 100:.2f}")
        
    def update_transcription_cost(self):
        """Update transcription cost estimation display."""
        try:
            service = self.transcription_service.currentText()
            
            if service == "openai":
                cost_text = [
                    "📊 OpenAI Whisper Pricing:",
                    "  • $0.006 per minute",
                    "  • $0.36 per hour",
                    "  • $8.64 per day (24h)",
                    "",
                    "Example costs:",
                    "  • 5-minute meeting: $0.03",
                    "  • 30-minute interview: $0.18",
                    "  • 2-hour recording: $0.72"
                ]
            else:
                cost_text = [
                    "📊 Local Whisper Pricing:",
                    "  • $0.00 - Completely free!",
                    "  • Uses your computer's CPU/GPU",
                    "  • No internet required",
                    "",
                    "Trade-offs:",
                    "  • Slower processing time",
                    "  • Uses local computing power",
                    "  • Complete privacy (offline)"
                ]
            
            self.transcription_cost_label.setText("\n".join(cost_text))
            
        except Exception as e:
            logger.error(f"Transcription cost estimation error: {e}")
            self.transcription_cost_label.setText("Cost estimation unavailable")
        
    def on_summarization_toggled(self, enabled: bool):
        """Handle summarization toggle."""
        self.summary_group.setEnabled(enabled)
        self.update_cost_estimation()
        
    def validate_api_key(self):
        """Validate the OpenAI API key with a live API check."""
        api_key = self.openai_api_key.text().strip()
        if not api_key:
            self._update_api_key_status("not_configured", "No API key entered")
            return

        # Format check first (instant feedback)
        if not self.settings_manager.validate_openai_api_key(api_key):
            self._update_api_key_status("invalid", "Invalid format. Key must start with 'sk-' and be at least 20 characters.")
            return

        # Disable button and show progress
        self.validate_key_button.setText("Validating...")
        self.validate_key_button.setEnabled(False)
        self._update_api_key_status("checking", "Validating API key...")

        # Start live validation in background
        self.validator_thread = APIKeyValidator(self.settings_manager, api_key)
        self.validator_thread.validation_complete.connect(self.on_validation_complete)
        self.validator_thread.start()

    def on_validation_complete(self, success: bool, message: str):
        """Handle API key validation completion."""
        self.validate_key_button.setText("Validate")
        self.validate_key_button.setEnabled(True)

        if success:
            self._update_api_key_status("valid", message)
        else:
            self._update_api_key_status("invalid", message)

    def _update_api_key_status(self, status: str, message: str):
        """Update the API key status indicator.

        Args:
            status: One of 'valid', 'invalid', 'not_configured', 'checking'
            message: Status message to display
        """
        styles = {
            "valid": "color: #4CAF50; font-weight: bold;",
            "invalid": "color: #F44336; font-weight: bold;",
            "not_configured": "color: #FF9800; font-weight: bold;",
            "checking": "color: #2196F3; font-style: italic;",
        }
        icons = {
            "valid": "Valid",
            "invalid": "Invalid",
            "not_configured": "Not Configured",
            "checking": "Checking...",
        }
        style = styles.get(status, "")
        icon = icons.get(status, "")
        self.api_key_status_label.setStyleSheet(style)
        self.api_key_status_label.setText(f"Status: {icon} - {message}")

    def _refresh_api_key_status(self):
        """Refresh the API key status based on current state."""
        if self.settings_manager.has_openai_api_key():
            method = self.settings_manager.get_api_key_storage_method()
            method_labels = {
                "keyring": "system keyring",
                "encrypted_config": "encrypted config",
                "environment": "environment variable",
            }
            label = method_labels.get(method, method)
            self._update_api_key_status(
                "valid",
                f"Key configured (stored in {label})"
            )
        else:
            self._update_api_key_status("not_configured", "No API key configured")
            
    def update_cost_estimation(self):
        """Update simplified cost estimation display."""
        try:
            service = self.transcription_service.currentText()
            include_summary = self.summarization_enabled.isChecked()
            duration_hours = self.duration_spinbox.value()
            
            # Static cost estimates (approximate)
            if service == "openai":
                # OpenAI Whisper: $0.006 per minute
                transcription_cost_per_hour = 0.006 * 60  # $0.36/hour
                service_name = "OpenAI Whisper API"
            else:
                # Local Whisper: Free
                transcription_cost_per_hour = 0.0
                service_name = "Local Whisper"
                
            # AI Summary costs (if enabled)
            if include_summary:
                model = self.summary_model.currentText()
                if "gpt-4" in model:
                    summary_cost_per_hour = 0.03  # ~$0.03 per summary
                elif "gpt-3.5" in model:
                    summary_cost_per_hour = 0.002  # ~$0.002 per summary
                else:
                    summary_cost_per_hour = 0.01  # Default estimate
            else:
                summary_cost_per_hour = 0.0
                
            # Calculate total costs
            transcription_total = transcription_cost_per_hour * duration_hours
            summary_total = summary_cost_per_hour * duration_hours
            total_cost = transcription_total + summary_total
                
            # Create detailed breakdown
            breakdown_lines = [
                f"📋 Cost Breakdown for {duration_hours:.1f} hour(s):",
                f"{'─' * 40}",
                f"Service: {service_name}"
            ]
            
            if service == "openai":
                breakdown_lines.append(f"Transcription: ${transcription_total:.4f}")
            else:
                breakdown_lines.append("Transcription: $0.0000 (Local)")
                
            if include_summary:
                model = self.summary_model.currentText()
                max_tokens = self.max_tokens.value()
                breakdown_lines.extend([
                    f"AI Summary ({model}): ${summary_total:.4f}",
                    f"  └─ Max tokens: {max_tokens}"
                ])
            else:
                breakdown_lines.append("AI Summary: $0.0000 (Disabled)")
                
            breakdown_lines.extend([
                f"{'─' * 40}",
                f"TOTAL: ${total_cost:.4f}"
            ])
            
            # Calculate per-hour rate
            if duration_hours > 0:
                hourly_rate = total_cost / duration_hours
                breakdown_lines.append(f"Per hour: ${hourly_rate:.4f}")
                
            self.cost_breakdown.setText("\n".join(breakdown_lines))
            
            # Update total cost display
            if duration_hours == 1.0:
                self.cost_total.setText(f"💰 Total estimated cost per hour: ${total_cost:.4f}")
            else:
                hourly_rate = total_cost / duration_hours if duration_hours > 0 else 0
                self.cost_total.setText(f"💰 Total: ${total_cost:.4f} (${hourly_rate:.4f}/hour)")
                
        except Exception as e:
            logger.error(f"Cost estimation error: {e}")
            self.cost_breakdown.setText(f"❌ Cost estimation error: {str(e)}")
            self.cost_total.setText("Cost estimation unavailable")
            
    def browse_recordings_dir(self):
        """Browse for recordings directory."""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Recordings Directory", self.recordings_dir.text()
        )
        if dir_path:
            self.recordings_dir.setText(dir_path)
            
    def browse_vault_dir(self):
        """Browse for vault directory."""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Vault Directory", self.vault_dir.text()
        )
        if dir_path:
            self.vault_dir.setText(dir_path)
            
    def update_storage_info(self):
        """Update storage information display."""
        try:
            recordings_path = Path(self.recordings_dir.text())
            vault_path = Path(self.vault_dir.text())
            
            info_text = []
            
            # Recordings info
            if recordings_path.exists():
                recordings_count = len(list(recordings_path.glob("*.wav")))
                info_text.append(f"Recordings: {recordings_count} files")
            else:
                info_text.append("Recordings directory: Not found")
                
            # Vault info
            if vault_path.exists():
                db_path = vault_path / "scribevault.db"
                if db_path.exists():
                    info_text.append(f"Vault database: {db_path.stat().st_size // 1024} KB")
                else:
                    info_text.append("Vault database: Not created")
            else:
                info_text.append("Vault directory: Not found")
                
            self.storage_info.setText("\n".join(info_text))
            
        except Exception as e:
            self.storage_info.setText(f"Error reading storage info: {e}")
            
    def load_current_settings(self):
        """Load current settings into the dialog."""
        try:
            settings = self.settings
            
            # Audio settings
            preset_index = self.audio_preset.findData(settings.audio.preset)
            if preset_index >= 0:
                self.audio_preset.setCurrentIndex(preset_index)
            self._on_audio_preset_changed(self.audio_preset.currentIndex())
            # Select saved input device
            if settings.audio.input_device_index is not None:
                dev_idx = self.audio_device.findData(
                    settings.audio.input_device_index
                )
                if dev_idx >= 0:
                    self.audio_device.setCurrentIndex(dev_idx)

            # Transcription settings
            self.transcription_service.setCurrentText(settings.transcription.service)
            self.openai_model.setCurrentText(settings.transcription.openai_model)
            self.local_model.setCurrentText(settings.transcription.local_model)
            self.device.setCurrentText(settings.transcription.device)
            self.language.setCurrentText(settings.transcription.language)
            
            # Load API key and update status
            api_key = self.settings_manager.get_openai_api_key()
            if api_key:
                self.openai_api_key.setText(api_key)
            self._refresh_api_key_status()
                
            # Diarization settings
            self.diarization_enabled.setChecked(settings.diarization.enabled)
            self.diarization_speaker_count.setValue(settings.diarization.num_speakers)
            self.diarization_sensitivity.setValue(
                int(settings.diarization.sensitivity * 100)
            )
            self._on_diarization_toggled(settings.diarization.enabled)

            # Summarization settings
            self.summarization_enabled.setChecked(settings.summarization.enabled)
            self.summary_service.setCurrentText(settings.summarization.service)
            self.summary_model.setCurrentText(settings.summarization.model)
            self.summary_style.setCurrentText(settings.summarization.style)
            self.max_tokens.setValue(settings.summarization.max_tokens)
            
            # UI settings
            self.theme.setCurrentText(settings.ui.theme)
            self.window_width.setValue(settings.ui.window_width)
            self.window_height.setValue(settings.ui.window_height)
            self.auto_save.setChecked(settings.ui.auto_save)
            
            # Storage settings
            self.recordings_dir.setText(settings.recordings_dir)
            self.vault_dir.setText(settings.vault_dir)
            
            # Update UI state
            self.on_transcription_service_changed(settings.transcription.service)
            self.on_summarization_toggled(settings.summarization.enabled)
            
            # Trigger cost estimation updates
            QTimer.singleShot(200, self.update_cost_estimation)
            QTimer.singleShot(200, self.update_transcription_cost)
            
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            QMessageBox.warning(self, "Settings Error", f"Error loading settings: {e}")
            
    def save_settings(self):
        """Save settings and close dialog."""
        try:
            # Create new audio settings
            preset_key = self.audio_preset.currentData() or "standard"
            preset_params = AUDIO_PRESETS.get(preset_key, AUDIO_PRESETS["standard"])
            device_data = self.audio_device.currentData()
            device_name = self.audio_device.currentText()
            audio = AudioSettings(
                preset=preset_key,
                sample_rate=preset_params["sample_rate"],
                channels=preset_params["channels"],
                input_device_index=device_data,
                input_device_name=device_name,
            )

            # Create new settings objects
            transcription = TranscriptionSettings(
                service=self.transcription_service.currentText(),
                openai_model=self.openai_model.currentText(),
                local_model=self.local_model.currentText(),
                device=self.device.currentText(),
                language=self.language.currentText()
            )
            
            summarization = SummarizationSettings(
                enabled=self.summarization_enabled.isChecked(),
                service=self.summary_service.currentText(),
                model=self.summary_model.currentText(),
                style=self.summary_style.currentText(),
                max_tokens=self.max_tokens.value()
            )
            
            diarization = DiarizationSettings(
                enabled=self.diarization_enabled.isChecked(),
                num_speakers=self.diarization_speaker_count.value(),
                sensitivity=self.diarization_sensitivity.value() / 100.0,
            )

            ui = UISettings(
                theme=self.theme.currentText(),
                window_width=self.window_width.value(),
                window_height=self.window_height.value(),
                auto_save=self.auto_save.isChecked()
            )

            # Update settings manager
            self.settings_manager.settings.audio = audio
            self.settings_manager.settings.transcription = transcription
            self.settings_manager.settings.summarization = summarization
            self.settings_manager.settings.diarization = diarization
            self.settings_manager.settings.ui = ui
            self.settings_manager.settings.recordings_dir = self.recordings_dir.text()
            self.settings_manager.settings.vault_dir = self.vault_dir.text()
            
            # Save API key if provided (with format validation)
            api_key = self.openai_api_key.text().strip()
            if api_key:
                if not self.settings_manager.validate_openai_api_key(api_key):
                    reply = QMessageBox.warning(
                        self,
                        "Invalid API Key Format",
                        "The API key format appears invalid (must start with 'sk-' "
                        "and be at least 20 characters).\n\n"
                        "Save anyway?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No,
                    )
                    if reply != QMessageBox.Yes:
                        return
                self.settings_manager.save_openai_api_key(api_key)
                
            # Save settings to file
            self.settings_manager.save_settings()
            
            QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully!")
            self.accept()
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            QMessageBox.critical(self, "Save Error", f"Error saving settings: {e}")
            
    def show_service_comparison(self):
        """Show simplified service comparison dialog."""
        try:
            duration_hours = self.duration_spinbox.value()
            include_summary = self.summarization_enabled.isChecked()
            
            # Static cost estimates
            # OpenAI costs
            openai_transcription = 0.006 * 60 * duration_hours  # $0.006/min
            openai_summary = 0.01 * duration_hours if include_summary else 0  # ~$0.01/hour estimate
            openai_total = openai_transcription + openai_summary
            
            # Local costs (free transcription, still need OpenAI for summary)
            local_transcription = 0.0
            local_summary = 0.01 * duration_hours if include_summary else 0
            local_total = local_transcription + local_summary
            
            # Create comparison dialog
            comparison_dialog = QDialog(self)
            comparison_dialog.setWindowTitle("Service Cost Comparison")
            comparison_dialog.setMinimumSize(500, 400)
            
            layout = QVBoxLayout(comparison_dialog)
            
            # Title
            title = QLabel(f"📊 Service Comparison for {duration_hours:.1f} hour(s)")
            title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
            title.setAlignment(Qt.AlignCenter)
            layout.addWidget(title)
            
            # Comparison table
            comparison_text = QTextEdit()
            comparison_text.setReadOnly(True)
            comparison_text.setStyleSheet("font-family: 'Courier New', monospace;")
            
            comparison_content = self._generate_simple_comparison(
                openai_transcription, openai_summary, openai_total,
                local_transcription, local_summary, local_total,
                duration_hours, include_summary
            )
            comparison_text.setPlainText(comparison_content)
            
            layout.addWidget(comparison_text)
            
            # Recommendations
            recommendations = self._generate_simple_recommendations(openai_total, local_total)
            rec_label = QLabel(f"💡 Recommendations:\n{recommendations}")
            rec_label.setStyleSheet("color: #4CAF50; font-style: italic; margin: 10px;")
            rec_label.setWordWrap(True)
            layout.addWidget(rec_label)
            
            # Close button
            close_button = QPushButton("Close")
            close_button.clicked.connect(comparison_dialog.accept)
            layout.addWidget(close_button)
            
            comparison_dialog.exec()
            
        except Exception as e:
            logger.error(f"Service comparison error: {e}")
            QMessageBox.warning(self, "Comparison Error", f"Failed to generate comparison: {e}")
            
    def _generate_simple_comparison(self, openai_trans, openai_sum, openai_total, 
                                   local_trans, local_sum, local_total, duration_hours, include_summary):
        """Generate simplified comparison content."""
        lines = [
            "╔══════════════════════════════════════════════════════════╗",
            "║                    SERVICE COMPARISON                    ║",
            "╠══════════════════════════════════════════════════════════╣",
            "║                    │    OpenAI API    │  Local Whisper  ║",
            "╠════════════════════╪══════════════════╪══════════════════╣"
        ]
        
        # Transcription costs
        lines.append(f"║ Transcription      │    ${openai_trans:>8.4f}      │    ${local_trans:>8.4f}      ║")
        
        # Summary costs
        if include_summary:
            lines.append(f"║ AI Summary         │    ${openai_sum:>8.4f}      │    ${local_sum:>8.4f}      ║")
        
        # Totals
        lines.extend([
            "╠════════════════════╪══════════════════╪══════════════════╣",
            f"║ TOTAL              │    ${openai_total:>8.4f}      │    ${local_total:>8.4f}      ║"
        ])
        
        # Per hour rates
        if duration_hours > 0:
            openai_hourly = openai_total / duration_hours
            local_hourly = local_total / duration_hours
            lines.append(f"║ Per Hour           │    ${openai_hourly:>8.4f}      │    ${local_hourly:>8.4f}      ║")
        
        lines.extend([
            "╚════════════════════╧══════════════════╧══════════════════╝",
            "",
            "FEATURE COMPARISON:",
            "┌─────────────────────────────────────────────────────────┐",
            "│ OpenAI API:                                             │",
            "│  ✓ Highest accuracy                                     │",
            "│  ✓ Fast processing                                      │",
            "│  ✓ No local compute required                            │",
            "│  ✗ Requires internet connection                         │",
            "│  ✗ Per-minute billing                                   │",
            "│  ✗ Data sent to external service                        │",
            "│                                                         │",
            "│ Local Whisper:                                          │",
            "│  ✓ Complete privacy (offline)                           │",
            "│  ✓ No transcription costs                               │",
            "│  ✓ Works without internet                               │",
            "│  ✗ Requires local compute power                         │",
            "│  ✗ Slower on CPU                                        │",
            "│  ✗ Model accuracy varies by size                        │",
            "└─────────────────────────────────────────────────────────┘"
        ])
        
        return "\n".join(lines)
        
    def _generate_simple_recommendations(self, openai_total, local_total):
        """Generate simplified cost-based recommendations."""
        if local_total == 0:
            return ("• Local Whisper is free for transcription\n"
                   "• OpenAI API offers better accuracy but costs money\n"
                   "• Try local first, upgrade to OpenAI if needed")
        elif openai_total < local_total:
            savings = local_total - openai_total
            return (f"• OpenAI API is ${savings:.4f} cheaper for this usage\n"
                   "• Consider OpenAI for cost efficiency\n"
                   "• Local processing may still be worth it for privacy")
        else:
            savings = openai_total - local_total
            return (f"• Local Whisper saves ${savings:.4f}\n"
                   "• Free local processing recommended\n"
                   "• Good for high-volume usage")
                   
    def test_settings(self):
        """Test current settings."""
        # TODO: Implement settings testing
        QMessageBox.information(
            self, 
            "Test Settings", 
            "Settings testing is not yet implemented.\n"
            "This feature will validate your configuration."
        )
        
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to their defaults?\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Create default settings
            default_settings = AppSettings(
                transcription=TranscriptionSettings(),
                summarization=SummarizationSettings(),
                diarization=DiarizationSettings(),
                ui=UISettings(),
                audio=AudioSettings(),
                recordings_dir="recordings",
                vault_dir="vault"
            )
            
            self.settings_manager.settings = default_settings
            self.load_current_settings()
            
            QMessageBox.information(self, "Reset Complete", "Settings have been reset to defaults.")
