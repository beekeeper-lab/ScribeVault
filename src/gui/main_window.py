"""
Main application window for ScribeVault.
"""

import customtkinter as ctk
import os
from pathlib import Path
from dotenv import load_dotenv
import threading
from typing import Optional
import logging
import traceback
from datetime import datetime

from audio.recorder import AudioRecorder, AudioException
from transcription.whisper_service import WhisperService, TranscriptionException
from ai.summarizer import SummarizerService
from vault.manager import VaultManager, VaultException
from config.settings import SettingsManager
from gui.settings_window import SettingsWindow
from gui.assets import AssetManager

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GUIException(Exception):
    """Custom exception for GUI-related errors."""
    pass

class ScribeVaultApp:
    """Main application class for ScribeVault."""
    
    def __init__(self):
        """Initialize the ScribeVault application with proper error handling."""
        try:
            # Set appearance mode and theme
            ctk.set_appearance_mode("dark")  # "system", "dark", "light"
            ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"
            
            # Create main window
            self.root = ctk.CTk()
            self.root.title("ScribeVault")
            self.root.geometry("1200x800")
            self.root.minsize(800, 600)
            
            # Initialize services with error handling
            self._initialize_services()
            
            # Initialize state
            self.is_recording = False
            self.current_recording_path: Optional[Path] = None
            self._processing_thread: Optional[threading.Thread] = None
            
            # Setup UI
            self.setup_ui()
            
            # Set window icon
            self._set_window_icon()
            
            # Setup cleanup on window close
            self.root.protocol("WM_DELETE_WINDOW", self._on_window_closing)
            
            logger.info("ScribeVault application initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ScribeVault application: {e}")
            logger.error(traceback.format_exc())
            raise GUIException(f"Application initialization failed: {e}")
    
    def _initialize_services(self):
        """Initialize all services with proper error handling."""
        try:
            self.settings_manager = SettingsManager()
            logger.info("Settings manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize settings manager: {e}")
            raise GUIException(f"Settings initialization failed: {e}")
        
        try:
            self.asset_manager = AssetManager()
            logger.info("Asset manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize asset manager: {e}")
            raise GUIException(f"Asset manager initialization failed: {e}")
        
        try:
            self.audio_recorder = AudioRecorder()
            logger.info("Audio recorder initialized")
        except Exception as e:
            logger.error(f"Failed to initialize audio recorder: {e}")
            raise GUIException(f"Audio recorder initialization failed: {e}")
        
        try:
            self.whisper_service = WhisperService(self.settings_manager)
            logger.info("Whisper service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize whisper service: {e}")
            raise GUIException(f"Whisper service initialization failed: {e}")
        
        try:
            self.summarizer_service = SummarizerService()
            logger.info("Summarizer service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize summarizer service: {e}")
            raise GUIException(f"Summarizer service initialization failed: {e}")
        
        try:
            self.vault_manager = VaultManager()
            logger.info("Vault manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize vault manager: {e}")
            raise GUIException(f"Vault manager initialization failed: {e}")
    
    def _on_window_closing(self):
        """Handle window closing with proper cleanup."""
        try:
            logger.info("Application closing - performing cleanup")
            
            # Stop any ongoing recording
            if self.is_recording:
                logger.info("Stopping recording before shutdown")
                self._emergency_stop_recording()
            
            # Wait for processing thread to complete
            if self._processing_thread and self._processing_thread.is_alive():
                logger.info("Waiting for processing thread to complete")
                self._processing_thread.join(timeout=5.0)  # Wait max 5 seconds
            
            # Cleanup services
            self._cleanup_services()
            
            logger.info("Cleanup completed, destroying window")
            self.root.destroy()
            
        except Exception as e:
            logger.error(f"Error during application shutdown: {e}")
            self.root.destroy()  # Force close even if cleanup fails
    
    def _cleanup_services(self):
        """Cleanup all services properly."""
        try:
            if hasattr(self, 'audio_recorder') and self.audio_recorder:
                self.audio_recorder.cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up audio recorder: {e}")
    
    def _emergency_stop_recording(self):
        """Emergency stop recording without error propagation."""
        try:
            self.audio_recorder.stop_recording()
            self.is_recording = False
        except Exception as e:
            logger.error(f"Error in emergency stop recording: {e}")
            # Don't propagate errors during emergency shutdown
        
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
        """Set the window icon with proper error handling."""
        try:
            icon_path = self.asset_manager.get_icon_path("app_icon.png")
            if icon_path.exists():
                # For PNG icons, we need to convert to PhotoImage
                icon_image = self.asset_manager.get_app_icon(size=(32, 32))
                if icon_image:
                    # Note: CustomTkinter windows use iconphoto for PNG
                    # self.root.iconphoto(True, icon_image._light_image)
                    pass  # Commented out as it might not work with CTkImage directly
                    logger.info("Window icon loaded successfully")
            else:
                logger.warning("Icon file not found, using default window icon")
        except Exception as e:
            logger.error(f"Could not set window icon: {e}")
            # Don't raise - this is not critical for application functionality
            
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
        
        # Markdown button (hidden by default, appears when markdown is available)
        self.markdown_button = ctk.CTkButton(
            self.buttons_frame,
            text="📄 Markdown",
            command=self._open_current_markdown,
            height=40,
            width=100,
            font=ctk.CTkFont(size=14),
            fg_color="#6b46c1",  # Purple
            hover_color="#553c9a"
        )
        # Initially hidden - will be shown when markdown is available
        self._current_markdown_path = None
        
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
        
        # Wait for window to be visible before grabbing
        vault_window.update_idletasks()
        vault_window.after(100, lambda: vault_window.grab_set())
        
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
        
        # Debug: Print what we got
        print(f"DEBUG: Found {len(recordings)} recordings in vault")
        if recordings:
            for i, rec in enumerate(recordings[:3]):  # Show first 3
                print(f"  {i+1}. {rec['filename']} - Title: {rec.get('title', 'None')}")
        
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
        
        # Action buttons (right side)
        button_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        button_frame.pack(side="right", padx=5)
        
        # Delete button
        delete_button = ctk.CTkButton(
            button_frame,
            text="🗑️ Delete",
            command=lambda r=recording: self._delete_recording(r, parent),
            width=80,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#d32f2f",
            hover_color="#b71c1c"
        )
        delete_button.pack(side="right", padx=2)
        
        # View button
        view_button = ctk.CTkButton(
            button_frame,
            text="👁️ View",
            command=lambda r=recording: self._view_recording_details(r),
            width=80,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#666666",
            hover_color="#555555"
        )
        view_button.pack(side="right", padx=2)
        
        date_label = ctk.CTkLabel(
            header_frame,
            text=f"📅 {recording['created_at'][:16]}",  # Show date and time
            font=ctk.CTkFont(size=12)
        )
        date_label.pack(side="right", padx=(5, 10))
        
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
    
    def _delete_recording(self, recording, parent_widget):
        """Delete a recording with confirmation dialog.
        
        Args:
            recording: Recording data dictionary
            parent_widget: Parent widget to refresh
        """
        print(f"DEBUG: Starting delete process for recording {recording['id']}")
        
        # Create confirmation dialog
        confirm_window = ctk.CTkToplevel(self.root)
        confirm_window.title("Confirm Delete")
        confirm_window.geometry("450x250")
        confirm_window.transient(self.root)
        confirm_window.resizable(False, False)
        
        # Center the dialog
        confirm_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 450) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 250) // 2
        confirm_window.geometry(f"+{x}+{y}")
        
        # Focus window and bring to front
        confirm_window.lift()
        confirm_window.focus_force()
        confirm_window.attributes('-topmost', True)  # Force on top
        confirm_window.after(100, lambda: confirm_window.attributes('-topmost', False))  # Remove topmost after showing
        
        print("DEBUG: Confirmation window created and positioned")
        
        # Main content frame
        main_frame = ctk.CTkFrame(confirm_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Define the actions first
        def confirm_delete():
            print("DEBUG: confirm_delete function called")
            try:
                recording_id = recording['id']
                print(f"DEBUG: Attempting to delete recording ID {recording_id}")
                # Delete from database
                if self.vault_manager.delete_recording(recording_id):
                    # Try to delete the audio file too
                    audio_file = Path("recordings") / recording['filename']
                    if audio_file.exists():
                        audio_file.unlink()
                        print(f"DEBUG: Audio file {audio_file} deleted")
                        
                    self.update_status(f"✅ Recording '{recording['filename']}' deleted successfully")
                    
                    # Close confirmation dialog
                    confirm_window.destroy()
                    
                    # Close and reopen vault window to refresh
                    for widget in self.root.winfo_children():
                        if isinstance(widget, ctk.CTkToplevel) and "Vault" in widget.title():
                            widget.destroy()
                    self.show_vault()
                    
                else:
                    print("DEBUG: Database deletion failed")
                    self.update_status("❌ Failed to delete recording")
                    confirm_window.destroy()
                    
            except Exception as e:
                print(f"DEBUG: Exception in confirm_delete: {str(e)}")
                self.update_status(f"❌ Error deleting recording: {str(e)}")
                confirm_window.destroy()
        
        def cancel_action():
            print("DEBUG: Cancel button clicked")
            confirm_window.destroy()
            
        def delete_action():
            print("DEBUG: Delete button clicked")
            confirm_delete()

        # Keyboard bindings for accessibility
        def on_escape(event):
            print("DEBUG: Escape key pressed")
            cancel_action()
            
        def on_enter(event):
            print("DEBUG: Enter key pressed")
            delete_action()
            
        # Bind keyboard events
        confirm_window.bind('<Escape>', on_escape)
        confirm_window.bind('<Return>', on_enter)
        confirm_window.focus_set()  # Ensure window can receive keyboard events

        # Bind keyboard events
        confirm_window.bind('<Escape>', on_escape)
        confirm_window.bind('<Return>', on_enter)
        confirm_window.focus_set()  # Ensure window can receive keyboard events
        
        # Warning message
        warning_label = ctk.CTkLabel(
            main_frame,
            text="⚠️ Delete Recording",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="red"
        )
        warning_label.pack(pady=(10, 20))
        
        filename_label = ctk.CTkLabel(
            main_frame,
            text=f"Are you sure you want to delete:\n{recording['filename']}",
            font=ctk.CTkFont(size=14),
            wraplength=350
        )
        filename_label.pack(pady=10)
        
        warning_text = ctk.CTkLabel(
            main_frame,
            text="This action cannot be undone.",
            font=ctk.CTkFont(size=12),
            text_color="red"
        )
        warning_text.pack(pady=5)

        # Button frame
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(20, 10))
        
        # Try using standard tkinter buttons as a test
        import tkinter as tk
        
        # Create buttons with tkinter instead of customtkinter
        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            command=cancel_action,
            width=12,
            height=2,
            bg="#666666",
            fg="white",
            font=("Arial", 11)
        )
        cancel_button.pack(side="left", padx=(10, 5), pady=5)
        
        delete_button = tk.Button(
            button_frame,
            text="Delete",
            command=delete_action,
            width=12,
            height=2,
            bg="#d32f2f",
            fg="white",
            font=("Arial", 11)
        )
        delete_button.pack(side="right", padx=(5, 10), pady=5)
        
        print("DEBUG: Tkinter buttons created and packed successfully")
        print("DEBUG: You can also use Escape to cancel or Enter to delete")
        
        # Ensure the window gets focus after creation
        confirm_window.after(200, lambda: confirm_window.focus_force())
        
        # Set grab to make it modal, but do it safely
        def safe_grab():
            try:
                if confirm_window.winfo_exists():
                    confirm_window.grab_set()
                    print("DEBUG: Window grab set successfully")
            except Exception as e:
                print(f"DEBUG: Could not set grab: {e}")
                
        confirm_window.after(300, safe_grab)
    
    def _view_recording_details(self, recording):
        """View detailed information about a recording.
        
        Args:
            recording: Recording data dictionary
        """
        # Create details window
        details_window = ctk.CTkToplevel(self.root)
        details_window.title(f"Recording Details - {recording.get('title', recording['filename'])}")
        details_window.geometry("700x600")
        details_window.transient(self.root)  # Make it a child of main window, not vault window
        
        # Center the details window on the main window
        details_window.update_idletasks()
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y() 
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()
        
        detail_width = 700
        detail_height = 600
        x = main_x + (main_width - detail_width) // 2
        y = main_y + (main_height - detail_height) // 2
        details_window.geometry(f"+{x}+{y}")
        
        # Force window to front and grab focus
        details_window.lift()
        details_window.focus_force()
        details_window.after(100, lambda: details_window.grab_set())
        
        # Configure grid
        details_window.grid_columnconfigure(0, weight=1)
        details_window.grid_rowconfigure(0, weight=1)
        
        # Create scrollable content
        content_frame = ctk.CTkScrollableFrame(details_window)
        content_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        # Display recording details
        try:
            self._display_recording_details(content_frame, recording)
        except Exception as e:
            # If there's an error displaying details, show debug info
            error_label = ctk.CTkLabel(
                content_frame,
                text=f"Error displaying details: {str(e)}",
                font=ctk.CTkFont(size=14),
                text_color="red"
            )
            error_label.pack(pady=20)
            
            # Show raw recording data for debugging
            debug_text = ctk.CTkTextbox(content_frame, height=200)
            debug_text.pack(fill="x", pady=10)
            debug_text.insert("1.0", f"Recording data:\n{recording}")
            debug_text.configure(state="disabled")
        
        # Action buttons at bottom
        button_frame = ctk.CTkFrame(details_window)
        button_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        # Determine number of buttons to adjust grid
        button_count = 2  # Edit and Close are always present
        if Path("recordings") / recording['filename'] and (Path("recordings") / recording['filename']).exists():
            button_count += 1  # Play button
        if recording.get('markdown_path') and Path(recording['markdown_path']).exists():
            button_count += 1  # Markdown button
            
        # Configure grid columns
        for i in range(button_count):
            button_frame.grid_columnconfigure(i, weight=1)
        
        current_column = 0
        
        # Edit button
        edit_button = ctk.CTkButton(
            button_frame,
            text="✏️ Edit",
            command=lambda: self._edit_recording(recording, details_window),
            width=100
        )
        edit_button.grid(row=0, column=current_column, padx=5, pady=10)
        current_column += 1
        
        # Play audio button (if file exists)
        audio_file = Path("recordings") / recording['filename']
        if audio_file.exists():
            play_button = ctk.CTkButton(
                button_frame,
                text="🔊 Play Audio",
                command=lambda: self._play_audio(audio_file),
                width=100,
                fg_color="#4a7c7e",
                hover_color="#3a6466"
            )
            play_button.grid(row=0, column=current_column, padx=5, pady=10)
            current_column += 1
        
        # Open markdown button (if markdown file exists)
        if recording.get('markdown_path') and Path(recording['markdown_path']).exists():
            markdown_button = ctk.CTkButton(
                button_frame,
                text="📄 View Summary",
                command=lambda: self._view_markdown_summary(recording['markdown_path'], recording.get('title', recording['filename'])),
                width=120,  # Made slightly wider
                height=35,  # Made slightly taller
                fg_color="#8b5cf6",  # Brighter purple
                hover_color="#7c3aed",
                font=ctk.CTkFont(size=13, weight="bold")  # Bold font
            )
            markdown_button.grid(row=0, column=current_column, padx=8, pady=10)  # More padding
            current_column += 1
        
        # Close button
        close_button = ctk.CTkButton(
            button_frame,
            text="Close",
            command=details_window.destroy,
            width=100
        )
        close_button.grid(row=0, column=current_column, padx=5, pady=10)
    
    def _open_markdown_file(self, markdown_path: str):
        """Open the markdown summary file in the default application.
        
        Args:
            markdown_path: Path to the markdown file
        """
        try:
            import platform
            import subprocess
            
            markdown_file = Path(markdown_path)
            
            if not markdown_file.exists():
                self._safe_status_update(f"Markdown file not found: {markdown_path}")
                return
            
            # Open file with system default application
            system = platform.system()
            if system == "Windows":
                os.startfile(str(markdown_file))
            elif system == "Darwin":  # macOS
                subprocess.run(["open", str(markdown_file)])
            else:  # Linux and other Unix-like systems
                subprocess.run(["xdg-open", str(markdown_file)])
            
            self._safe_status_update(f"Opened markdown file: {markdown_file.name}")
            
        except Exception as e:
            logger.error(f"Failed to open markdown file: {e}")
            self._safe_status_update(f"Failed to open markdown file: {e}")
    
    def _open_current_markdown(self):
        """Open the current recording's markdown file in the internal viewer."""
        if self._current_markdown_path:
            # Get title from current recording if available
            current_title = "Summary"
            if hasattr(self, '_current_recording_data') and self._current_recording_data:
                current_title = self._current_recording_data.get('title') or self._current_recording_data.get('filename', 'Summary')
            
            self._view_markdown_summary(self._current_markdown_path, current_title)
        else:
            self._safe_status_update("No markdown file available")
    
    def _view_markdown_summary(self, markdown_path: str, title: str = "Summary"):
        """View markdown summary in an internal viewer window.
        
        Args:
            markdown_path: Path to the markdown file
            title: Title for the viewer window
        """
        try:
            markdown_file = Path(markdown_path)
            
            if not markdown_file.exists():
                self._safe_status_update(f"Markdown file not found: {markdown_path}")
                return
            
            # Read markdown content
            with open(markdown_file, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # Create markdown viewer window
            viewer_window = ctk.CTkToplevel(self.root)
            viewer_window.title(f"Summary - {title}")
            viewer_window.geometry("900x700")
            viewer_window.transient(self.root)
            
            # Center the viewer window
            viewer_window.update_idletasks()
            main_x = self.root.winfo_x()
            main_y = self.root.winfo_y()
            main_width = self.root.winfo_width()
            main_height = self.root.winfo_height()
            
            viewer_width = 900
            viewer_height = 700
            x = main_x + (main_width - viewer_width) // 2
            y = main_y + (main_height - viewer_height) // 2
            viewer_window.geometry(f"+{x}+{y}")
            
            # Force window to front
            viewer_window.lift()
            viewer_window.focus_force()
            
            # Configure grid properly for the viewer window
            viewer_window.grid_columnconfigure(0, weight=1)
            viewer_window.grid_rowconfigure(0, weight=1)  # Make content row expandable
            
            # Create content area with proper scrolling (no header frame)
            content_frame = ctk.CTkFrame(viewer_window)
            content_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
            content_frame.grid_columnconfigure(0, weight=1)
            content_frame.grid_rowconfigure(0, weight=1)
            
            # Create scrollable textbox for markdown content
            content_text = ctk.CTkTextbox(
                content_frame,
                font=ctk.CTkFont(family="Segoe UI", size=14),
                wrap="word"
            )
            content_text.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
            
            # Insert the formatted markdown content
            self._format_markdown_content(content_text, markdown_content)
            content_text.configure(state="disabled")  # Make it read-only
            
            # Button frame
            button_frame = ctk.CTkFrame(viewer_window)
            button_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
            
            # Buttons
            open_external_button = ctk.CTkButton(
                button_frame,
                text="🔗 Open External",
                command=lambda: self._open_markdown_file(markdown_path),
                width=120,
                fg_color="#4a7c7e",
                hover_color="#3a6466"
            )
            open_external_button.pack(side="left", padx=(15, 5), pady=10)
            
            copy_button = ctk.CTkButton(
                button_frame,
                text="📋 Copy Text",
                command=lambda: self._copy_to_clipboard(markdown_content),
                width=120,
                fg_color="#6b7280",
                hover_color="#5b6572"
            )
            copy_button.pack(side="left", padx=5, pady=10)
            
            close_button = ctk.CTkButton(
                button_frame,
                text="Close",
                command=viewer_window.destroy,
                width=80
            )
            close_button.pack(side="right", padx=(5, 15), pady=10)
            
            self._safe_status_update(f"Opened summary viewer: {markdown_file.name}")
            
        except Exception as e:
            logger.error(f"Failed to view markdown summary: {e}")
            self._safe_status_update(f"Failed to view summary: {e}")
    
    def _format_markdown_content(self, text_widget, markdown_content: str):
        """Format markdown content with proper styling in a text widget.
        
        Args:
            text_widget: The CTkTextbox to insert formatted content into
            markdown_content: The raw markdown content to format
        """
        try:
            # Clear the widget first
            text_widget.delete("1.0", "end")
            
            # Simple markdown processing - convert to readable format
            lines = markdown_content.split('\n')
            formatted_lines = []
            
            for line in lines:
                # Process different markdown elements
                if line.startswith('# '):
                    # H1 heading - make it prominent
                    formatted_lines.append(f"\n{'=' * 60}")
                    formatted_lines.append(f"  {line[2:].upper()}")
                    formatted_lines.append(f"{'=' * 60}\n")
                    
                elif line.startswith('## '):
                    # H2 heading
                    formatted_lines.append(f"\n{'-' * 50}")
                    formatted_lines.append(f"  {line[3:]}")
                    formatted_lines.append(f"{'-' * 50}\n")
                    
                elif line.startswith('### '):
                    # H3 heading  
                    formatted_lines.append(f"\n▶ {line[4:]}")
                    formatted_lines.append("")
                    
                elif line.startswith('**') and line.endswith('**:'):
                    # Bold labels (like "Date:", "Category:", etc.)
                    formatted_lines.append(f"📋 {line[2:-3]}: ")
                    
                elif line.startswith('- '):
                    # Bullet points
                    formatted_lines.append(f"   • {line[2:]}")
                    
                elif line.startswith('```'):
                    # Code blocks - just remove the backticks
                    if line == '```':
                        formatted_lines.append("")
                    else:
                        formatted_lines.append(line[3:])
                    
                elif line.strip() == '---':
                    # Horizontal rule
                    formatted_lines.append(f"\n{'─' * 60}\n")
                    
                elif '**' in line:
                    # Handle inline bold text - remove asterisks
                    clean_line = line.replace('**', '')
                    formatted_lines.append(clean_line)
                    
                else:
                    # Regular text
                    formatted_lines.append(line)
            
            # Join all lines and insert into text widget
            formatted_text = '\n'.join(formatted_lines)
            text_widget.insert("1.0", formatted_text)
            
        except Exception as e:
            logger.error(f"Error formatting markdown: {e}")
            # Fallback to plain text
            text_widget.insert("1.0", markdown_content)
    
    def _copy_to_clipboard(self, text: str):
        """Copy text content to clipboard.
        
        Args:
            text: Text to copy to clipboard
        """
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self._safe_status_update("Summary copied to clipboard")
        except Exception as e:
            logger.error(f"Failed to copy to clipboard: {e}")
            self._safe_status_update("Failed to copy to clipboard")
    
    def _display_recording_details(self, parent, recording):
        """Display detailed recording information.
        
        Args:
            parent: Parent widget
            recording: Recording data dictionary
        """
        # Title
        title = recording.get('title') or recording['filename']
        title_label = ctk.CTkLabel(
            parent,
            text=title,
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(anchor="w", pady=(0, 20))
        
        # Metadata section
        meta_frame = ctk.CTkFrame(parent)
        meta_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            meta_frame,
            text="📋 Metadata",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        # Format metadata
        created_at = recording.get('created_at', 'Unknown')
        duration = recording.get('duration', 0)
        file_size = recording.get('file_size', 0)
        
        # Format duration
        if duration > 0:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            duration_str = f"{minutes}:{seconds:02d}"
        else:
            duration_str = "Unknown"
            
        # Format file size
        if file_size > 0:
            size_mb = file_size / (1024 * 1024)
            size_str = f"{size_mb:.1f} MB"
        else:
            size_str = "Unknown"
        
        metadata = [
            ("Filename", recording.get('filename', 'Unknown')),
            ("Category", recording.get('category', 'other').title()),
            ("Date Created", created_at[:16] if created_at else 'Unknown'),
            ("Duration", duration_str),
            ("File Size", size_str),
            ("Recording ID", str(recording.get('id', 'Unknown')))
        ]
        
        for label, value in metadata:
            meta_row = ctk.CTkFrame(meta_frame, fg_color="transparent")
            meta_row.pack(fill="x", padx=15, pady=2)
            
            ctk.CTkLabel(
                meta_row,
                text=f"{label}:",
                font=ctk.CTkFont(weight="bold"),
                width=120,
                anchor="w"
            ).pack(side="left")
            
            ctk.CTkLabel(
                meta_row,
                text=value,
                anchor="w"
            ).pack(side="left", padx=(10, 0))
        
        # Description (if exists)
        if recording.get('description'):
            desc_frame = ctk.CTkFrame(parent)
            desc_frame.pack(fill="x", pady=(0, 20))
            
            ctk.CTkLabel(
                desc_frame,
                text="📝 Description",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(anchor="w", padx=15, pady=(15, 10))
            
            desc_text = ctk.CTkTextbox(desc_frame, height=80)
            desc_text.pack(fill="x", padx=15, pady=(0, 15))
            desc_text.insert("1.0", recording['description'])
            desc_text.configure(state="disabled")
        
        # Transcription
        if recording.get('transcription'):
            trans_frame = ctk.CTkFrame(parent)
            trans_frame.pack(fill="x", pady=(0, 20))
            
            ctk.CTkLabel(
                trans_frame,
                text="🎤 Transcription",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(anchor="w", padx=15, pady=(15, 10))
            
            trans_text = ctk.CTkTextbox(trans_frame, height=200)
            trans_text.pack(fill="x", padx=15, pady=(0, 15))
            trans_text.insert("1.0", recording['transcription'])
            trans_text.configure(state="disabled")
        
        # Summary
        if recording.get('summary'):
            summary_frame = ctk.CTkFrame(parent)
            summary_frame.pack(fill="x", pady=(0, 20))
            
            ctk.CTkLabel(
                summary_frame,
                text="🤖 AI Summary",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(anchor="w", padx=15, pady=(15, 10))
            
            summary_text = ctk.CTkTextbox(summary_frame, height=120)
            summary_text.pack(fill="x", padx=15, pady=(0, 15))
            summary_text.insert("1.0", recording['summary'])
            summary_text.configure(state="disabled")
            
        # Key points (if exists)
        if recording.get('key_points'):
            points_frame = ctk.CTkFrame(parent)
            points_frame.pack(fill="x", pady=(0, 20))
            
            ctk.CTkLabel(
                points_frame,
                text="🎯 Key Points",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(anchor="w", padx=15, pady=(15, 10))
            
            try:
                import json
                key_points = json.loads(recording['key_points']) if isinstance(recording['key_points'], str) else recording['key_points']
                for i, point in enumerate(key_points, 1):
                    point_label = ctk.CTkLabel(
                        points_frame,
                        text=f"{i}. {point}",
                        font=ctk.CTkFont(size=12),
                        anchor="w"
                    )
                    point_label.pack(anchor="w", padx=25, pady=2)
            except:
                # If parsing fails, show raw text
                points_text = ctk.CTkTextbox(points_frame, height=60)
                points_text.pack(fill="x", padx=15, pady=(0, 15))
                points_text.insert("1.0", str(recording['key_points']))
                points_text.configure(state="disabled")
    
    def _edit_recording(self, recording, parent_window):
        """Edit recording metadata.
        
        Args:
            recording: Recording data dictionary
            parent_window: Parent window to close after editing
        """
        # Create edit window
        edit_window = ctk.CTkToplevel(self.root)
        edit_window.title(f"Edit Recording - {recording['filename']}")
        edit_window.geometry("500x400")
        edit_window.transient(parent_window)
        edit_window.grab_set()
        
        # Center the edit window
        edit_window.update_idletasks()
        x = parent_window.winfo_x() + 50
        y = parent_window.winfo_y() + 50
        edit_window.geometry(f"+{x}+{y}")
        
        # Create form
        main_frame = ctk.CTkFrame(edit_window)
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Title field
        ctk.CTkLabel(main_frame, text="Title:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        title_entry = ctk.CTkEntry(main_frame, width=400)
        title_entry.pack(padx=10, pady=(0, 10), fill="x")
        title_entry.insert(0, recording.get('title', ''))
        
        # Description field
        ctk.CTkLabel(main_frame, text="Description:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        desc_text = ctk.CTkTextbox(main_frame, height=100)
        desc_text.pack(padx=10, pady=(0, 10), fill="x")
        desc_text.insert("1.0", recording.get('description', ''))
        
        # Category field
        ctk.CTkLabel(main_frame, text="Category:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        category_var = ctk.StringVar(value=recording.get('category', 'other'))
        category_menu = ctk.CTkOptionMenu(
            main_frame,
            variable=category_var,
            values=["meeting", "interview", "lecture", "note", "other"]
        )
        category_menu.pack(padx=10, pady=(0, 20), fill="x")
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=10)
        
        def save_changes():
            try:
                # Update recording in database
                success = self.vault_manager.update_recording(
                    recording['id'],
                    title=title_entry.get().strip(),
                    description=desc_text.get("1.0", "end-1c").strip(),
                    category=category_var.get()
                )
                
                if success:
                    self.update_status(f"✅ Recording '{recording['filename']}' updated successfully")
                    edit_window.destroy()
                    parent_window.destroy()
                    
                    # Refresh vault
                    for widget in self.root.winfo_children():
                        if isinstance(widget, ctk.CTkToplevel) and "Vault" in widget.title():
                            widget.destroy()
                    self.show_vault()
                else:
                    self.update_status("❌ Failed to update recording")
                    
            except Exception as e:
                self.update_status(f"❌ Error updating recording: {str(e)}")
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=edit_window.destroy,
            width=100
        )
        cancel_button.pack(side="left", padx=5)
        
        save_button = ctk.CTkButton(
            button_frame,
            text="Save Changes",
            command=save_changes,
            width=120,
            fg_color="#4a7c7e",
            hover_color="#3a6466"
        )
        save_button.pack(side="right", padx=5)
    
    def _play_audio(self, audio_file):
        """Play an audio file using system default player.
        
        Args:
            audio_file: Path to the audio file
        """
        try:
            import subprocess
            import platform
            
            system = platform.system()
            if system == "Windows":
                os.startfile(audio_file)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", str(audio_file)])
            else:  # Linux
                subprocess.run(["xdg-open", str(audio_file)])
                
            self.update_status(f"🔊 Playing {audio_file.name}")
            
        except Exception as e:
            self.update_status(f"❌ Could not play audio: {str(e)}")
        
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
        """Start audio recording with comprehensive error handling."""
        try:
            if self.is_recording:
                logger.warning("Recording already in progress")
                return
            
            # Validate audio recorder state
            if not hasattr(self, 'audio_recorder') or not self.audio_recorder:
                raise GUIException("Audio recorder not initialized")
            
            logger.info("Starting audio recording")
            
            # Update UI state first
            self.is_recording = True
            self._safe_ui_update(lambda: self._update_recording_ui(True))
            self._safe_status_update("Starting recording...")
            
            # Start recording
            self.current_recording_path = self.audio_recorder.start_recording()
            
            self._safe_status_update("Recording audio...")
            logger.info(f"Recording started: {self.current_recording_path}")
            
        except AudioException as e:
            logger.error(f"Audio recording error: {e}")
            self._handle_recording_error(f"Audio system error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error starting recording: {e}")
            logger.error(traceback.format_exc())
            self._handle_recording_error(f"Failed to start recording: {e}")
    
    def stop_recording(self):
        """Stop audio recording with comprehensive error handling."""
        try:
            if not self.is_recording:
                logger.warning("No recording in progress")
                return
            
            logger.info("Stopping audio recording")
            
            # Update UI state first
            self.is_recording = False
            self._safe_ui_update(lambda: self._update_recording_ui(False))
            self._safe_status_update("Stopping recording...")
            
            # Stop recording and get the file path
            recorded_file = self.audio_recorder.stop_recording()
            
            if recorded_file and recorded_file.exists():
                logger.info(f"Recording stopped: {recorded_file}")
                self._safe_status_update("Processing recording...")
                
                # Start processing in a separate thread
                self._processing_thread = threading.Thread(
                    target=self._process_recording_safe, 
                    args=(recorded_file,),
                    daemon=True
                )
                self._processing_thread.start()
            else:
                logger.warning("No valid recording file produced")
                self._safe_status_update("No recording to process")
                
        except AudioException as e:
            logger.error(f"Audio recording error: {e}")
            self._handle_recording_error(f"Audio system error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error stopping recording: {e}")
            logger.error(traceback.format_exc())
            self._handle_recording_error(f"Failed to stop recording: {e}")
    
    def _handle_recording_error(self, error_message: str):
        """Handle recording errors with proper UI state reset."""
        self.is_recording = False
        self._safe_ui_update(lambda: self._update_recording_ui(False))
        self._safe_status_update(error_message)
    
    def _update_recording_ui(self, is_recording: bool):
        """Update recording UI elements safely."""
        try:
            if is_recording:
                self.record_button.configure(
                    text="⏹️ Stop Recording", 
                    fg_color="red", 
                    hover_color="#cc0000"
                )
                self.recording_indicator.configure(text="🔴 Recording...")
            else:
                self.record_button.configure(
                    text="🎙️ Start Recording", 
                    fg_color="#1f538d", 
                    hover_color="#164a7b"
                )
                self.recording_indicator.configure(text="")
        except Exception as e:
            logger.error(f"Error updating recording UI: {e}")
    
    def _safe_ui_update(self, update_func):
        """Safely update UI from any thread."""
        try:
            if self.root and self.root.winfo_exists():
                self.root.after(0, update_func)
        except Exception as e:
            logger.error(f"Error in safe UI update: {e}")
    
    def _safe_status_update(self, message: str):
        """Safely update status from any thread."""
        try:
            if self.root and self.root.winfo_exists():
                self.root.after(0, lambda: self.update_status(message))
        except Exception as e:
            logger.error(f"Error in safe status update: {e}")
        
    def _process_recording_safe(self, audio_path):
        """Thread-safe wrapper for recording processing."""
        try:
            self._process_recording(audio_path)
        except Exception as e:
            logger.error(f"Critical error in recording processing: {e}")
            logger.error(traceback.format_exc())
            self._safe_status_update(f"Processing failed: {e}")
        
    def _process_recording(self, audio_path):
        """Process the recorded audio file with transcription and summarization."""
        try:
            if not audio_path or not audio_path.exists():
                raise GUIException(f"Invalid audio file: {audio_path}")
            
            logger.info(f"Processing recording: {audio_path}")
            
            # Update status on main thread
            self._safe_status_update("Transcribing audio...")
            
            # Transcribe the audio
            transcript = self.whisper_service.transcribe_audio(audio_path)
            
            if not transcript or not transcript.strip():
                raise TranscriptionException("No transcript generated")
            
            logger.info("Transcription completed successfully")
            
            summary = None
            markdown_path = None
            
            # Generate summary only if checkbox is checked
            if self.summarize_var.get():
                self._safe_status_update("Generating summary...")
                try:
                    # Prepare recording data for markdown generation
                    recording_data = {
                        'filename': audio_path.name,
                        'transcription': transcript,
                        'file_size': audio_path.stat().st_size,
                        'duration': self._get_audio_duration(audio_path),
                        'created_at': datetime.now().isoformat(),
                        'category': 'other'  # Default category, can be changed later
                    }
                    
                    # Use the new summarize_with_markdown method
                    summary_result = self.summarizer_service.generate_summary_with_markdown(recording_data)
                    
                    summary = summary_result.get('summary')
                    markdown_path = summary_result.get('markdown_path')
                    
                    if summary:
                        logger.info("Summary generated successfully")
                        if markdown_path:
                            logger.info(f"Markdown file generated: {markdown_path}")
                    
                    if summary_result.get('error'):
                        logger.warning(f"Summary generation warning: {summary_result['error']}")
                        
                except Exception as e:
                    logger.error(f"Summary generation failed: {e}")
                    # Continue without summary rather than failing completely
                    summary = None
                    markdown_path = None
            
            # Save to vault with validation
            try:
                recording_id = self.vault_manager.add_recording(
                    filename=audio_path.name,
                    transcription=transcript,
                    summary=summary,
                    file_size=audio_path.stat().st_size,
                    duration=self._get_audio_duration(audio_path),
                    markdown_path=markdown_path
                )
                
                logger.info(f"Recording saved to vault with ID: {recording_id}")
                
                # Update status
                status_msg = f"Recording saved! (ID: {recording_id})"
                if not self.summarize_var.get():
                    status_msg += " - Summary skipped"
                elif not summary:
                    status_msg += " - Summary failed"
                elif markdown_path:
                    status_msg += f" - Summary & markdown generated"
                else:
                    status_msg += " - Summary generated (markdown failed)"
                
                self._safe_status_update(status_msg)
                
                # Show results in the main content area
                self._safe_ui_update(lambda: self._show_recording_result(transcript, summary, markdown_path))
                
            except VaultException as e:
                logger.error(f"Failed to save recording to vault: {e}")
                self._safe_status_update(f"Save failed: {e}")
                # Still show the results even if saving failed
                self._safe_ui_update(lambda: self._show_recording_result(transcript, summary, markdown_path))
                
        except TranscriptionException as e:
            logger.error(f"Transcription failed: {e}")
            self._safe_status_update(f"Transcription failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error processing recording: {e}")
            logger.error(traceback.format_exc())
            self._safe_status_update(f"Processing error: {e}")
    
    def _get_audio_duration(self, audio_path):
        """Get audio duration safely."""
        try:
            # This would need actual audio duration calculation
            # For now, return 0 as placeholder
            return 0.0
        except Exception as e:
            logger.error(f"Error getting audio duration: {e}")
            return 0.0
            
    def _show_recording_result(self, transcript, summary, markdown_path=None):
        """Show the recording result in the text areas with validation."""
        try:
            # Validate text areas exist
            if not hasattr(self, 'transcript_text') or self.transcript_text is None:
                logger.error("Transcript text area not initialized")
                return
                
            if not hasattr(self, 'summary_text') or self.summary_text is None:
                logger.error("Summary text area not initialized") 
                return
            
            # Update transcript area
            self.transcript_text.configure(state="normal")
            self.transcript_text.delete("1.0", "end")
            if transcript:
                self.transcript_text.insert("1.0", transcript)
            else:
                self.transcript_text.insert("1.0", "No transcript available")
            self.transcript_text.configure(state="disabled")
            
            # Update summary area
            self.summary_text.configure(state="normal")
            self.summary_text.delete("1.0", "end")
            
            if summary:
                summary_display = summary
                # Add markdown file notice if available
                if markdown_path and Path(markdown_path).exists():
                    summary_display += f"\n\n📄 Markdown summary saved: {Path(markdown_path).name}"
                self.summary_text.insert("1.0", summary_display)
            else:
                # Check if summary was skipped or failed
                summary_message = ("Summary generation was skipped" 
                                 if not self.summarize_var.get() 
                                 else "Summary generation failed")
                self.summary_text.insert("1.0", summary_message)
                
            self.summary_text.configure(state="disabled")
            
            # Store markdown path for potential access
            self._current_markdown_path = markdown_path
            
            # Show/hide markdown button based on availability
            if markdown_path and Path(markdown_path).exists():
                self.markdown_button.grid(row=0, column=3, padx=(0, 10))
            else:
                self.markdown_button.grid_forget()
            
            logger.info("Recording results displayed successfully")
            
        except Exception as e:
            logger.error(f"Error displaying recording results: {e}")
            logger.error(traceback.format_exc())
            
    def update_status(self, message: str):
        """Update the status bar message with validation."""
        try:
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.configure(text=message)
                logger.debug(f"Status updated: {message}")
            else:
                logger.warning(f"Status label not available, message: {message}")
        except Exception as e:
            logger.error(f"Error updating status: {e}")
        
    def run(self):
        """Start the application main loop with error handling."""
        try:
            logger.info("Starting ScribeVault application")
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Application crashed: {e}")
            logger.error(traceback.format_exc())
            raise
