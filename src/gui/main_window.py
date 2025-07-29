"""
Main application window for ScribeVault.
"""

import customtkinter as ctk
import os
from pathlib import Path
from dotenv import load_dotenv
import threading
from typing import Optional

from audio.recorder import AudioRecorder
from transcription.whisper_service import WhisperService
from ai.summarizer import SummarizerService
from vault.manager import VaultManager
from config.settings import SettingsManager
from gui.settings_window import SettingsWindow

# Load environment variables
load_dotenv()

class ScribeVaultApp:
    """Main application class for ScribeVault."""
    
    def __init__(self):
        """Initialize the ScribeVault application."""
        # Set appearance mode and theme
        ctk.set_appearance_mode("dark")  # "system", "dark", "light"
        ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title("ScribeVault")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Initialize services
        self.settings_manager = SettingsManager()
        self.audio_recorder = AudioRecorder()
        self.whisper_service = WhisperService(self.settings_manager)
        self.summarizer_service = SummarizerService()
        self.vault_manager = VaultManager()
        
        # Initialize state
        self.is_recording = False
        self.current_recording_path: Optional[Path] = None
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface."""
        # Configure grid
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Create sidebar
        self.create_sidebar()
        
        # Create main content area
        self.create_main_content()
        
        # Create status bar
        self.create_status_bar()
        
    def create_sidebar(self):
        """Create the sidebar with navigation and controls."""
        self.sidebar_frame = ctk.CTkFrame(self.root, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)
        
        # App title
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="ScribeVault", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Record button
        self.record_button = ctk.CTkButton(
            self.sidebar_frame,
            text="🎙️ Start Recording",
            command=self.toggle_recording,
            height=40,
            font=ctk.CTkFont(size=16)
        )
        self.record_button.grid(row=1, column=0, padx=20, pady=10)
        
        # Summarization checkbox
        self.summarize_var = ctk.BooleanVar(value=self.settings_manager.settings.summarization.enabled)
        self.summarize_checkbox = ctk.CTkCheckBox(
            self.sidebar_frame,
            text="📝 Generate Summary",
            variable=self.summarize_var,
            font=ctk.CTkFont(size=14)
        )
        self.summarize_checkbox.grid(row=2, column=0, padx=20, pady=(0, 10))
        
        # Navigation buttons
        self.vault_button = ctk.CTkButton(
            self.sidebar_frame,
            text="📚 Vault",
            command=self.show_vault,
            height=35
        )
        self.vault_button.grid(row=3, column=0, padx=20, pady=5)
        
        self.settings_button = ctk.CTkButton(
            self.sidebar_frame,
            text="⚙️ Settings",
            command=self.show_settings,
            height=35
        )
        self.settings_button.grid(row=4, column=0, padx=20, pady=5)
        
        # Recording indicator
        self.recording_indicator = ctk.CTkLabel(
            self.sidebar_frame,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.recording_indicator.grid(row=6, column=0, padx=20, pady=10)
        
    def create_main_content(self):
        """Create the main content area."""
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.grid(row=0, column=1, columnspan=2, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # Welcome message
        self.welcome_label = ctk.CTkLabel(
            self.main_frame,
            text="Welcome to ScribeVault",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.welcome_label.grid(row=0, column=0, padx=20, pady=20)
        
        # Content area (will be replaced with different views)
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        # Initial content
        self.show_welcome()
        
    def create_status_bar(self):
        """Create the status bar."""
        self.status_frame = ctk.CTkFrame(self.root, height=30)
        self.status_frame.grid(row=1, column=1, columnspan=2, padx=20, pady=(0, 20), sticky="ew")
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
    def show_welcome(self):
        """Show the welcome screen."""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        welcome_text = ctk.CTkLabel(
            self.content_frame,
            text="Click 'Start Recording' to begin capturing audio.\nYour recordings will be automatically transcribed and summarized.",
            font=ctk.CTkFont(size=16),
            justify="center"
        )
        welcome_text.pack(expand=True, pady=50)
        
    def show_vault(self):
        """Show the vault/library view."""
        self.update_status("Loading vault...")
        
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        # Create vault interface
        vault_frame = ctk.CTkFrame(self.content_frame)
        vault_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = ctk.CTkLabel(
            vault_frame,
            text="📚 Recording Vault",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=10)
        
        # Get recordings from database
        recordings = self.vault_manager.get_recordings(limit=50)
        
        if not recordings:
            # No recordings message
            no_recordings_label = ctk.CTkLabel(
                vault_frame,
                text="No recordings found. Start recording to build your vault!",
                font=ctk.CTkFont(size=14)
            )
            no_recordings_label.pack(pady=20)
        else:
            # Create scrollable frame for recordings
            scrollable_frame = ctk.CTkScrollableFrame(vault_frame)
            scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Display each recording
            for recording in recordings:
                self._create_recording_card(scrollable_frame, recording)
                
        self.update_status(f"Loaded {len(recordings)} recordings")
        
    def _create_recording_card(self, parent, recording):
        """Create a card widget for displaying a recording."""
        # Recording card frame
        card_frame = ctk.CTkFrame(parent)
        card_frame.pack(fill="x", padx=5, pady=5)
        
        # Header with filename and date
        header_frame = ctk.CTkFrame(card_frame)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        filename_label = ctk.CTkLabel(
            header_frame,
            text=f"🎵 {recording['filename']}",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        filename_label.pack(side="left", padx=5)
        
        date_label = ctk.CTkLabel(
            header_frame,
            text=f"📅 {recording['created_at'][:16]}",  # Show date and time
            font=ctk.CTkFont(size=12)
        )
        date_label.pack(side="right", padx=5)
        
        # Transcription preview
        if recording['transcription']:
            trans_preview = recording['transcription'][:100] + "..." if len(recording['transcription']) > 100 else recording['transcription']
            trans_label = ctk.CTkLabel(
                card_frame,
                text=f"📝 {trans_preview}",
                font=ctk.CTkFont(size=12),
                wraplength=400
            )
            trans_label.pack(anchor="w", padx=10, pady=2)
            
        # Summary preview
        if recording['summary']:
            summary_preview = recording['summary'][:80] + "..." if len(recording['summary']) > 80 else recording['summary']
            summary_label = ctk.CTkLabel(
                card_frame,
                text=f"💡 {summary_preview}",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            summary_label.pack(anchor="w", padx=10, pady=2)
        
    def show_settings(self):
        """Show the settings window."""
        settings_window = SettingsWindow(
            parent=self.root,
            settings_manager=self.settings_manager,
            on_settings_changed=self.on_settings_changed
        )
        
    def on_settings_changed(self):
        """Handle settings changes."""
        # Reinitialize services with new settings
        self.whisper_service = WhisperService(self.settings_manager)
        
        # Apply theme changes
        settings = self.settings_manager.settings
        if hasattr(settings.ui, 'theme'):
            ctk.set_appearance_mode(settings.ui.theme)
            
        self.update_status("Settings updated successfully")
        
    def toggle_recording(self):
        """Toggle audio recording on/off."""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
            
    def start_recording(self):
        """Start audio recording."""
        try:
            self.is_recording = True
            self.record_button.configure(text="⏹️ Stop Recording", fg_color="red")
            self.recording_indicator.configure(text="🔴 Recording...")
            self.update_status("Recording audio...")
            
            # Start recording in a separate thread
            self.current_recording_path = self.audio_recorder.start_recording()
            
        except Exception as e:
            self.update_status(f"Error starting recording: {e}")
            self.is_recording = False
            self.record_button.configure(text="🎙️ Start Recording")
            self.recording_indicator.configure(text="")
            
    def stop_recording(self):
        """Stop audio recording."""
        try:
            self.is_recording = False
            self.record_button.configure(text="🎙️ Start Recording")
            self.recording_indicator.configure(text="")
            self.update_status("Processing recording...")
            
            # Stop recording and get the file path
            recorded_file = self.audio_recorder.stop_recording()
            
            if recorded_file:
                # Start transcription and summarization in a separate thread
                processing_thread = threading.Thread(
                    target=self._process_recording, 
                    args=(recorded_file,)
                )
                processing_thread.daemon = True
                processing_thread.start()
            else:
                self.update_status("No recording to process")
                
        except Exception as e:
            self.update_status(f"Error stopping recording: {e}")
            self.is_recording = False
            self.record_button.configure(text="🎙️ Start Recording")
            self.recording_indicator.configure(text="")
        
    def _process_recording(self, audio_path):
        """Process the recorded audio file with transcription and summarization."""
        try:
            # Update status on main thread
            self.root.after(0, lambda: self.update_status("Transcribing audio..."))
            
            # Transcribe the audio
            transcript = self.whisper_service.transcribe_audio(audio_path)
            
            if transcript:
                summary = None
                
                # Generate summary only if checkbox is checked
                if self.summarize_var.get():
                    self.root.after(0, lambda: self.update_status("Generating summary..."))
                    summary = self.summarizer_service.summarize_text(transcript)
                
                # Save to vault
                recording_id = self.vault_manager.add_recording(
                    filename=audio_path.name,
                    transcription=transcript,
                    summary=summary,
                    file_size=audio_path.stat().st_size if audio_path.exists() else 0
                )
                
                # Update status
                status_msg = f"Recording saved! (ID: {recording_id})"
                if not self.summarize_var.get():
                    status_msg += " - Summary skipped"
                self.root.after(0, lambda: self.update_status(status_msg))
                
                # Show results in the main content area
                self.root.after(0, lambda: self._show_recording_result(transcript, summary))
                
            else:
                self.root.after(0, lambda: self.update_status("Transcription failed"))
                
        except Exception as e:
            self.root.after(0, lambda: self.update_status(f"Processing error: {e}"))
            
    def _show_recording_result(self, transcript, summary):
        """Show the recording result in the main content area."""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        # Create scrollable frame
        result_frame = ctk.CTkScrollableFrame(self.content_frame)
        result_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Transcript section
        transcript_label = ctk.CTkLabel(
            result_frame,
            text="Transcription:",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        transcript_label.pack(anchor="w", pady=(0, 5))
        
        transcript_text = ctk.CTkTextbox(result_frame, height=150)
        transcript_text.pack(fill="x", pady=(0, 20))
        transcript_text.insert("1.0", transcript)
        transcript_text.configure(state="disabled")
        
        # Summary section
        summary_label = ctk.CTkLabel(
            result_frame,
            text="Summary:",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        summary_label.pack(anchor="w", pady=(0, 5))
        
        if summary:
            summary_text = ctk.CTkTextbox(result_frame, height=100)
            summary_text.pack(fill="x", pady=(0, 20))
            summary_text.insert("1.0", summary)
            summary_text.configure(state="disabled")
        else:
            # Check if summary was skipped or failed
            summary_message = "Summary generation was skipped" if not self.summarize_var.get() else "Summary generation failed"
            summary_error = ctk.CTkLabel(
                result_frame,
                text=summary_message,
                text_color="gray" if not self.summarize_var.get() else "red"
            )
            summary_error.pack(anchor="w", pady=(0, 20))
            
        # Back button
        back_button = ctk.CTkButton(
            result_frame,
            text="Back to Home",
            command=self.show_welcome,
            height=35
        )
        back_button.pack(pady=10)
            
    def update_status(self, message: str):
        """Update the status bar message."""
        self.status_label.configure(text=message)
        
    def run(self):
        """Start the application main loop."""
        self.root.mainloop()
