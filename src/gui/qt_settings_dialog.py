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

from config.settings import SettingsManager, TranscriptionSettings, SummarizationSettings, UISettings, AudioSettings, AppSettings, AUDIO_PRESETS, CostEstimator
from gui.settings_diagnostics import run_all_checks, DiagnosticResult
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


class SettingsTestRunner(QThread):
    """Background thread to run diagnostic checks."""

    results_ready = Signal(list)  # List[DiagnosticResult]

    def __init__(self, settings_manager, recordings_dir, vault_dir,
                 device_index, needs_api_key):
        super().__init__()
        self.settings_manager = settings_manager
        self.recordings_dir = recordings_dir
        self.vault_dir = vault_dir
        self.device_index = device_index
        self.needs_api_key = needs_api_key

    def run(self):
        """Run all diagnostic checks in background."""
        try:
            results = run_all_checks(
                self.settings_manager,
                self.recordings_dir,
                self.vault_dir,
                self.device_index,
                self.needs_api_key,
            )
            self.results_ready.emit(results)
        except Exception as e:
            error_result = DiagnosticResult(
                name="Diagnostics", status="fail",
                message=f"Unexpected error: {e}",
            )
            self.results_ready.emit([error_result])


class SettingsDialog(QDialog):
    """Settings dialog for ScribeVault configuration."""
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.settings = settings_manager.settings
        self.validator_thread = None
        self.test_runner_thread = None

        self.setup_ui()
        self.load_current_settings()
        
    def setup_ui(self):
        """Setup the settings dialog UI."""
        self.setWindowTitle("Settings")
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
        
        # Cost estimation for transcription
        cost_group = QGroupBox("💰 Transcription Cost")
        cost_layout = QVBoxLayout(cost_group)
        
        self.transcription_cost_label = QLabel()
        self.transcription_cost_label.setStyleSheet("font-family: 'Courier New', monospace; font-size: 12px;")
        cost_layout.addWidget(self.transcription_cost_label)
        
        cost_info = QLabel(
            "💡 OpenAI charges $0.006 per minute ($0.36/hour). "
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

        # Settings group (Service dropdown removed — hardcoded to "openai")
        self.summary_group = QGroupBox("Summarization Settings")
        summary_layout = QGridLayout(self.summary_group)

        summary_layout.addWidget(QLabel("Model:"), 0, 0)
        self.summary_model = QComboBox()
        self._populate_summary_models()
        self.summary_model.currentTextChanged.connect(self.update_cost_estimation)
        summary_layout.addWidget(self.summary_model, 0, 1)

        summary_layout.addWidget(QLabel("Style:"), 1, 0)
        self.summary_style = QComboBox()
        self.summary_style.addItems(["concise", "detailed", "bullet_points"])
        summary_layout.addWidget(self.summary_style, 1, 1)

        summary_layout.addWidget(QLabel("Max Tokens:"), 2, 0)
        self.max_tokens = QSpinBox()
        self.max_tokens.setRange(100, 4000)
        self.max_tokens.setValue(500)
        self.max_tokens.valueChanged.connect(self.update_cost_estimation)
        summary_layout.addWidget(self.max_tokens, 2, 1)

        # Cost estimation
        cost_group = QGroupBox("Cost Estimation")
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
        self.compare_button = QPushButton("Compare Services")
        self.compare_button.clicked.connect(self.show_service_comparison)
        cost_layout.addWidget(self.compare_button)

        # Last Updated display and Update button
        update_layout = QHBoxLayout()
        self.last_updated_label = QLabel()
        self.last_updated_label.setStyleSheet("color: #888; font-size: 10px;")
        self._refresh_last_updated()
        update_layout.addWidget(self.last_updated_label)
        update_layout.addStretch()

        self.update_pricing_button = QPushButton("Update Models && Pricing")
        self.update_pricing_button.clicked.connect(self._on_update_pricing)
        update_layout.addWidget(self.update_pricing_button)
        cost_layout.addLayout(update_layout)

        cost_info = QLabel(
            "Costs are estimated based on current OpenAI pricing. "
            "Local Whisper transcription is free but requires computational resources. "
            "Actual costs may vary depending on audio quality and content length."
        )
        cost_info.setStyleSheet("color: #888; font-size: 10px; font-style: italic;")
        cost_info.setWordWrap(True)
        cost_layout.addWidget(cost_info)

        layout.addWidget(self.summary_group)
        layout.addWidget(cost_group)
        layout.addStretch()

        self.tab_widget.addTab(tab, "AI Summary")

    def _populate_summary_models(self):
        """Populate the summary model dropdown from CostEstimator config."""
        current = self.summary_model.currentText()
        self.summary_model.clear()
        models = CostEstimator.get_summary_models()
        if models:
            self.summary_model.addItems(models)
        else:
            self.summary_model.addItems(["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"])
        # Restore previous selection if still valid
        idx = self.summary_model.findText(current)
        if idx >= 0:
            self.summary_model.setCurrentIndex(idx)

    def _refresh_last_updated(self):
        """Update the Last Updated label from pricing config."""
        last_updated = CostEstimator.get_last_updated()
        self.last_updated_label.setText(f"Pricing last updated: {last_updated}")

    def _on_update_pricing(self):
        """Handle Update Models & Pricing button click."""
        CostEstimator.load_pricing()
        self._populate_summary_models()
        self._refresh_last_updated()
        self.update_cost_estimation()
        
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
        """Update cost estimation display using CostEstimator."""
        try:
            service = self.transcription_service.currentText()
            include_summary = self.summarization_enabled.isChecked()
            duration_hours = self.duration_spinbox.value()
            model = self.summary_model.currentText()
            minutes = duration_hours * 60

            if service == "openai":
                costs = CostEstimator.estimate_openai_cost(minutes, include_summary, model)
                service_name = "OpenAI Whisper API"
            else:
                costs = CostEstimator.estimate_local_cost(minutes, include_summary, model)
                service_name = "Local Whisper"

            transcription_total = costs["transcription"]
            summary_total = costs["summary"]
            total_cost = costs["total"]

            breakdown_lines = [
                f"Cost Breakdown for {duration_hours:.1f} hour(s):",
                f"{'─' * 40}",
                f"Service: {service_name}",
            ]

            if service == "openai":
                breakdown_lines.append(f"Transcription: ${transcription_total:.4f}")
            else:
                breakdown_lines.append("Transcription: $0.0000 (Local)")

            if include_summary:
                max_tokens = self.max_tokens.value()
                breakdown_lines.extend([
                    f"AI Summary ({model}): ${summary_total:.4f}",
                    f"  Max tokens: {max_tokens}",
                ])
            else:
                breakdown_lines.append("AI Summary: $0.0000 (Disabled)")

            breakdown_lines.extend([
                f"{'─' * 40}",
                f"TOTAL: ${total_cost:.4f}",
            ])

            if duration_hours > 0:
                hourly_rate = total_cost / duration_hours
                breakdown_lines.append(f"Per hour: ${hourly_rate:.4f}")

            self.cost_breakdown.setText("\n".join(breakdown_lines))

            if duration_hours == 1.0:
                self.cost_total.setText(f"Total estimated cost per hour: ${total_cost:.4f}")
            else:
                hourly_rate = total_cost / duration_hours if duration_hours > 0 else 0
                self.cost_total.setText(f"Total: ${total_cost:.4f} (${hourly_rate:.4f}/hour)")

        except Exception as e:
            logger.error(f"Cost estimation error: {e}")
            self.cost_breakdown.setText(f"Cost estimation error: {str(e)}")
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
                
            # Summarization settings
            self.summarization_enabled.setChecked(settings.summarization.enabled)
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
                service="openai",
                model=self.summary_model.currentText(),
                style=self.summary_style.currentText(),
                max_tokens=self.max_tokens.value()
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
            model = self.summary_model.currentText()
            minutes = duration_hours * 60

            comparison = CostEstimator.get_cost_comparison(minutes, include_summary, model)
            openai_transcription = comparison["openai"]["transcription"]
            openai_summary = comparison["openai"]["summary"]
            openai_total = comparison["openai"]["total"]
            local_transcription = comparison["local"]["transcription"]
            local_summary = comparison["local"]["summary"]
            local_total = comparison["local"]["total"]
            
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
        """Run diagnostic checks against current settings."""
        # Determine if an OpenAI API key is needed
        uses_openai_transcription = (
            self.transcription_service.currentText() == "openai"
        )
        uses_openai_summary = self.summarization_enabled.isChecked()
        needs_api_key = uses_openai_transcription or uses_openai_summary

        device_index = self.audio_device.currentData()

        # Disable button while checks run
        self.test_button.setText("Testing...")
        self.test_button.setEnabled(False)

        self.test_runner_thread = SettingsTestRunner(
            settings_manager=self.settings_manager,
            recordings_dir=self.recordings_dir.text(),
            vault_dir=self.vault_dir.text(),
            device_index=device_index,
            needs_api_key=needs_api_key,
        )
        self.test_runner_thread.results_ready.connect(
            self._on_test_results_ready
        )
        self.test_runner_thread.start()

    def _on_test_results_ready(self, results):
        """Display diagnostic results in a dialog."""
        self.test_button.setText("Test Settings")
        self.test_button.setEnabled(True)

        dialog = QDialog(self)
        dialog.setWindowTitle("Test Settings Results")
        dialog.setMinimumSize(450, 300)

        layout = QVBoxLayout(dialog)

        title = QLabel("Diagnostic Results")
        title.setStyleSheet(
            "font-size: 14px; font-weight: bold; margin-bottom: 8px;"
        )
        layout.addWidget(title)

        status_icons = {
            "pass": "\u2705",   # green check
            "fail": "\u274c",   # red X
            "skip": "\u2796",   # minus
            "warning": "\u26a0\ufe0f",  # warning
        }

        for result in results:
            row = QHBoxLayout()
            icon = status_icons.get(result.status, "?")
            icon_label = QLabel(icon)
            icon_label.setFixedWidth(30)
            row.addWidget(icon_label)

            text = QLabel(f"<b>{result.name}</b>: {result.message}")
            text.setWordWrap(True)
            row.addWidget(text, 1)

            layout.addLayout(row)

        # Summary line
        passed = sum(1 for r in results if r.status == "pass")
        failed = sum(1 for r in results if r.status == "fail")
        skipped = sum(1 for r in results if r.status == "skip")

        summary_parts = []
        if passed:
            summary_parts.append(f"{passed} passed")
        if failed:
            summary_parts.append(f"{failed} failed")
        if skipped:
            summary_parts.append(f"{skipped} skipped")

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        layout.addWidget(separator)

        summary = QLabel(", ".join(summary_parts))
        summary.setStyleSheet("font-weight: bold; margin-top: 4px;")
        layout.addWidget(summary)

        layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()
        
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
                ui=UISettings(),
                audio=AudioSettings(),
                recordings_dir="recordings",
                vault_dir="vault"
            )
            
            self.settings_manager.settings = default_settings
            self.load_current_settings()
            
            QMessageBox.information(self, "Reset Complete", "Settings have been reset to defaults.")
