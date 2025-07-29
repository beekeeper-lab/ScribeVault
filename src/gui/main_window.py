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
from gui.assets import AssetManager

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
        self.asset_manager = AssetManager()
        self.audio_recorder = AudioRecorder()
        self.whisper_service = WhisperService(self.settings_manager)
        self.summarizer_service = SummarizerService()
        self.vault_manager = VaultManager()
        
        # Initialize state
        self.is_recording = False
        self.current_recording_path: Optional[Path] = None
        
        # Setup UI
        self.setup_ui()
        
        # Set window icon
        self._set_window_icon()
        
    def setup_ui(self):
        """Set up the user interface."""
        # Configure grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Create main content area (no sidebar)
        self.create_main_content()
        
        # Create status bar
        self.create_status_bar()
        
    def _set_window_icon(self):
        """Set the window icon."""
        try:
            icon_path = self.asset_manager.get_icon_path("app_icon.png")
            if icon_path.exists():
                # For PNG icons, we need to convert to PhotoImage
                icon_image = self.asset_manager.get_app_icon(size=(32, 32))
                if icon_image:
                    # Note: CustomTkinter windows use iconphoto for PNG
                    # self.root.iconphoto(True, icon_image._light_image)
                    pass  # Commented out as it might not work with CTkImage directly
            else:
                print("Icon file not found, using default window icon")
        except Exception as e:
            print(f"Could not set window icon: {e}")
            
    def _create_branding_header(self):
        """Create the branding header with full-width blue background and larger logo."""
        # Header frame with full width and blue background matching logo
        self.header_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color="#2a2a2a",  # Neutral charcoal gray
            corner_radius=0,  # Sharp corners for full-width effect
            height=220  # Fixed height to accommodate larger logo
        )
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)  # Full width, no padding
        self.header_frame.grid_columnconfigure(0, weight=0)  # Don't expand, keep left-aligned
        self.header_frame.grid_columnconfigure(1, weight=1)  # Expand remaining space
        self.header_frame.grid_propagate(False)  # Maintain fixed height
        
        # Try to load logo image at larger size for better text readability
        logo_image = self.asset_manager.get_logo(size=(180, 180))  # Larger square logo
        
        if logo_image:
            # Use logo image positioned at far left with no top padding
            self.logo_display = ctk.CTkLabel(
                self.header_frame,
                image=logo_image,
                text=""  # No text when image is used
            )
            self.logo_display.grid(row=0, column=0, padx=(20, 0), pady=(10, 10), sticky="w")  # Left-aligned, minimal top padding
        else:
            # Fallback: larger centered text if no logo image
            self.logo_display = ctk.CTkLabel(
                self.header_frame,
                text="ScribeVault",
                font=ctk.CTkFont(size=32, weight="bold"),
                text_color="white"  # White text on blue background
            )
            self.logo_display.grid(row=0, column=0, pady=20)
        
    def _create_text_areas(self):
        """Create the transcribed text and AI summary areas."""
        # Transcribed Text section
        self.transcript_label = ctk.CTkLabel(
            self.main_frame,
            text="Transcribed Text",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        self.transcript_label.grid(row=1, column=0, padx=20, pady=(15, 5), sticky="w")  # Small space after header
        
        self.transcript_text = ctk.CTkTextbox(
            self.main_frame,
            height=150,
            corner_radius=8,
            fg_color="#F5F5F5",  # Light gray background
            text_color="#333333",  # Dark text for readability
            font=ctk.CTkFont(size=13)
        )
        self.transcript_text.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="nsew")
        
        # AI Summary section
        self.summary_label = ctk.CTkLabel(
            self.main_frame,
            text="AI Summary",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        self.summary_label.grid(row=3, column=0, padx=20, pady=(0, 5), sticky="w")
        
        self.summary_text = ctk.CTkTextbox(
            self.main_frame,
            height=100,
            corner_radius=8,
            fg_color="#F5F5F5",  # Light gray background
            text_color="#333333",  # Dark text for readability
            font=ctk.CTkFont(size=13)
        )
        self.summary_text.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="nsew")
        
        # Set initial placeholder text
        self.transcript_text.insert("1.0", "Click 'Start Recording' to begin capturing audio...")
        self.transcript_text.configure(state="disabled")
        
        self.summary_text.insert("1.0", "AI summary will appear here when enabled...")
        self.summary_text.configure(state="disabled")
        
    def _create_bottom_controls(self):
        """Create the bottom control panel with checkbox and buttons."""
        # Controls frame
        self.controls_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.controls_frame.grid(row=5, column=0, padx=20, pady=(10, 20), sticky="ew")
        self.controls_frame.grid_columnconfigure(1, weight=1)  # Expand middle space
        
        # Generate Summary checkbox (left side)
        self.summarize_var = ctk.BooleanVar(value=False)  # Unchecked by default
        self.summarize_checkbox = ctk.CTkCheckBox(
            self.controls_frame,
            text="Generate Summary",
            variable=self.summarize_var,
            font=ctk.CTkFont(size=14),
            command=self._on_summary_toggle
        )
        self.summarize_checkbox.grid(row=0, column=0, padx=(0, 20), pady=10, sticky="w")
        
        # Action buttons (right side)
        self.buttons_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        self.buttons_frame.grid(row=0, column=2, pady=10, sticky="e")
        
        # Start Recording button (highlighted in blue)
        self.record_button = ctk.CTkButton(
            self.buttons_frame,
            text="🎙️ Start Recording",
            command=self.toggle_recording,
            height=40,
            width=140,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#1f538d",  # Blue highlight
            hover_color="#164a7b"
        )
        self.record_button.grid(row=0, column=0, padx=(0, 10))
        
        # Vault button
        self.vault_button = ctk.CTkButton(
            self.buttons_frame,
            text="📚 Vault",
            command=self.show_vault,
            height=40,
            width=100,
            font=ctk.CTkFont(size=14),
            fg_color="#666666",  # Soft gray
            hover_color="#555555"
        )
        self.vault_button.grid(row=0, column=1, padx=(0, 10))
        
        # Settings button
        self.settings_button = ctk.CTkButton(
            self.buttons_frame,
            text="⚙️ Settings",
            command=self.show_settings,
            height=40,
            width=100,
            font=ctk.CTkFont(size=14),
            fg_color="#666666",  # Soft gray
            hover_color="#555555"
        )
        self.settings_button.grid(row=0, column=2)
        
    def _on_summary_toggle(self):
        """Handle summary checkbox toggle."""
        if self.summarize_var.get():
            self.summary_text.configure(fg_color="#F5F5F5")  # Normal color
            self.summary_label.configure(text_color=("gray10", "gray90"))  # Normal color
        else:
            self.summary_text.configure(fg_color="#E8E8E8")  # Dimmed color
            self.summary_label.configure(text_color="gray60")  # Dimmed color
        
    def create_main_content(self):
        """Create the main content area with new layout."""
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")  # No padding for full width
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)  # Text areas row
        self.main_frame.grid_rowconfigure(3, weight=1)  # Summary area row
        
        # Branding header (full-width)
        self._create_branding_header()
        
        # Text areas (with padding restored for content)
        self._create_text_areas()
        
        # Bottom controls
        self._create_bottom_controls()
        
    def create_status_bar(self):
        """Create the status bar."""
        self.status_frame = ctk.CTkFrame(self.root, height=30)
        self.status_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")  # Restore padding for status bar
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
        # Recording indicator in status bar
        self.recording_indicator = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.recording_indicator.pack(side="right", padx=10, pady=5)
        
    def show_vault(self):
        """Show the vault/library view in a new window."""
        self.update_status("Opening vault...")
        
        # Create vault window
        vault_window = ctk.CTkToplevel(self.root)
        vault_window.title("ScribeVault - Recording Vault")
        vault_window.geometry("800x600")
        vault_window.transient(self.root)
        vault_window.grab_set()
        
        # Configure grid
        vault_window.grid_columnconfigure(0, weight=1)
        vault_window.grid_rowconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            vault_window,
            text="📚 Recording Vault",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=20)
        
        # Get recordings from database
        recordings = self.vault_manager.get_recordings(limit=50)
        
        if not recordings:
            # No recordings message
            no_recordings_label = ctk.CTkLabel(
                vault_window,
                text="No recordings found. Start recording to build your vault!",
                font=ctk.CTkFont(size=14)
            )
            no_recordings_label.grid(row=1, column=0, pady=20)
        else:
            # Create scrollable frame for recordings
            scrollable_frame = ctk.CTkScrollableFrame(vault_window)
            scrollable_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
            
            # Display each recording
            for recording in recordings:
                self._create_recording_card(scrollable_frame, recording)
                
        self.update_status(f"Vault opened - {len(recordings)} recordings")
        
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
            self.record_button.configure(text="⏹️ Stop Recording", fg_color="red", hover_color="#cc0000")
            self.recording_indicator.configure(text="🔴 Recording...")
            self.update_status("Recording audio...")
            
            # Start recording in a separate thread
            self.current_recording_path = self.audio_recorder.start_recording()
            
        except Exception as e:
            self.update_status(f"Error starting recording: {e}")
            self.is_recording = False
            self.record_button.configure(text="🎙️ Start Recording", fg_color="#1f538d", hover_color="#164a7b")
            self.recording_indicator.configure(text="")
            
    def stop_recording(self):
        """Stop audio recording."""
        try:
            self.is_recording = False
            self.record_button.configure(text="🎙️ Start Recording", fg_color="#1f538d", hover_color="#164a7b")
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
            self.record_button.configure(text="🎙️ Start Recording", fg_color="#1f538d", hover_color="#164a7b")
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
        """Show the recording result in the text areas."""
        # Ensure text areas exist
        if not hasattr(self, 'transcript_text') or self.transcript_text is None:
            print("Error: Transcript text area not initialized")
            return
            
        if not hasattr(self, 'summary_text') or self.summary_text is None:
            print("Error: Summary text area not initialized") 
            return
        
        # Update transcript area
        self.transcript_text.configure(state="normal")
        self.transcript_text.delete("1.0", "end")
        self.transcript_text.insert("1.0", transcript)
        self.transcript_text.configure(state="disabled")
        
        # Update summary area
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        
        if summary:
            self.summary_text.insert("1.0", summary)
        else:
            # Check if summary was skipped or failed
            summary_message = "Summary generation was skipped" if not self.summarize_var.get() else "Summary generation failed"
            self.summary_text.insert("1.0", summary_message)
            
        self.summary_text.configure(state="disabled")
            
    def update_status(self, message: str):
        """Update the status bar message."""
        self.status_label.configure(text=message)
        
    def run(self):
        """Start the application main loop."""
        self.root.mainloop()
