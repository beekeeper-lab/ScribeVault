"""
Settings window for ScribeVault configuration.
"""

import customtkinter as ctk
from typing import Callable, Optional
from config.settings import SettingsManager, CostEstimator
from transcription.whisper_service import check_local_whisper_availability

class SettingsWindow:
    """Settings configuration window."""
    
    def __init__(self, parent, settings_manager: SettingsManager, on_settings_changed: Callable = None):
        """Initialize the settings window.
        
        Args:
            parent: Parent window
            settings_manager: Settings manager instance
            on_settings_changed: Callback when settings are changed
        """
        self.parent = parent
        self.settings_manager = settings_manager
        self.on_settings_changed = on_settings_changed
        
        # Create window
        self.window = ctk.CTkToplevel(parent)
        self.window.title("ScribeVault Settings")
        self.window.geometry("800x700")
        self.window.resizable(True, True)
        
        # Make window modal (but don't grab focus yet)
        self.window.transient(parent)
        
        # Center window
        self.window.update_idletasks()
        self._center_window()
        
        # Create UI
        self.setup_ui()
        self.load_current_settings()
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Now grab focus after everything is set up
        self.window.after(100, self._set_modal)
        
    def _center_window(self):
        """Center the window on the parent."""
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()
        
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
        
        self.window.geometry(f"+{x}+{y}")
        
    def _set_modal(self):
        """Set the window as modal after it's fully visible."""
        try:
            self.window.grab_set()
            self.window.focus_set()
        except Exception as e:
            # If grab fails, continue without modal behavior
            print(f"Warning: Could not set modal window: {e}")
        
    def setup_ui(self):
        """Create the settings UI."""
        # Configure grid
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(0, weight=1)
        
        # Create main scrollable frame
        self.main_frame = ctk.CTkScrollableFrame(self.window)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self.main_frame,
            text="⚙️ ScribeVault Settings",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Create sections
        self._create_transcription_section()
        self._create_cost_comparison_section()
        self._create_summarization_section()
        self._create_ui_section()
        
        # Action buttons
        self._create_action_buttons()
        
    def _create_transcription_section(self):
        """Create transcription settings section."""
        row = 1
        
        # Section title
        section_frame = ctk.CTkFrame(self.main_frame)
        section_frame.grid(row=row, column=0, sticky="ew", pady=(10, 0))
        section_frame.grid_columnconfigure(1, weight=1)
        
        title_label = ctk.CTkLabel(
            section_frame,
            text="🎤 Transcription Settings",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, padx=20, pady=15)
        
        # Service selection with explanation
        service_label = ctk.CTkLabel(
            section_frame, 
            text="Transcription Service:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        service_label.grid(row=1, column=0, padx=20, pady=(10, 5), sticky="w")
        
        # Service explanation
        explanation_text = (
            "Choose your transcription method:\n"
            "• Local Whisper: Free, private, runs on your computer (recommended)\n"
            "• OpenAI API: Fast, cloud-based, requires API key and costs money"
        )
        explanation_label = ctk.CTkLabel(
            section_frame,
            text=explanation_text,
            font=ctk.CTkFont(size=12),
            justify="left"
        )
        explanation_label.grid(row=1, column=1, padx=20, pady=(10, 5), sticky="w")
        
        self.service_var = ctk.StringVar(value="local")  # Default to local
        self.service_dropdown = ctk.CTkOptionMenu(
            section_frame,
            variable=self.service_var,
            values=["local", "openai"],  # Put local first
            command=self._on_service_changed
        )
        self.service_dropdown.grid(row=2, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
        
        # OpenAI settings frame
        self.openai_frame = ctk.CTkFrame(section_frame)
        self.openai_frame.grid(row=3, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        self.openai_frame.grid_columnconfigure(1, weight=1)
        
        openai_title = ctk.CTkLabel(
            self.openai_frame,
            text="☁️ OpenAI API Settings (Cloud Transcription)",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        openai_title.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        
        # Benefits and costs explanation
        openai_info = ctk.CTkLabel(
            self.openai_frame,
            text="Benefits: Very fast processing, excellent accuracy\nCosts: ~$0.006/minute ($0.36/hour) - requires API key",
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        openai_info.grid(row=1, column=0, columnspan=2, padx=10, pady=5)
        
        # API key status
        api_key_label = ctk.CTkLabel(self.openai_frame, text="API Key Status:")
        api_key_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")

        api_key_status = "✅ Configured" if self.settings_manager.has_openai_api_key() else "❌ Not configured"
        self.api_key_status_label = ctk.CTkLabel(
            self.openai_frame, 
            text=api_key_status,
            text_color="green" if self.settings_manager.has_openai_api_key() else "red"
        )
        self.api_key_status_label.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        # API key input
        api_key_input_label = ctk.CTkLabel(self.openai_frame, text="API Key:")
        api_key_input_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        
        # API key input frame (for entry + toggle button)
        api_key_frame = ctk.CTkFrame(self.openai_frame)
        api_key_frame.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        api_key_frame.grid_columnconfigure(0, weight=1)
        
        self.api_key_var = ctk.StringVar(value=self.settings_manager.get_openai_api_key() or "")
        self.api_key_entry = ctk.CTkEntry(
            api_key_frame,
            textvariable=self.api_key_var,
            placeholder_text="Enter your OpenAI API key (sk-...)",
            show="*",  # Start hidden for security
            width=300
        )
        self.api_key_entry.grid(row=0, column=0, padx=(5, 2), pady=5, sticky="ew")
        self.api_key_entry.bind("<KeyRelease>", self._on_api_key_changed)
        
        # Show/Hide toggle button
        self.api_key_visible = False
        self.toggle_button = ctk.CTkButton(
            api_key_frame,
            text="👁️",
            width=30,
            command=self._toggle_api_key_visibility
        )
        self.toggle_button.grid(row=0, column=1, padx=(2, 5), pady=5)
        
        # API key help
        api_help_label = ctk.CTkLabel(
            self.openai_frame,
            text="Get your API key from: https://platform.openai.com/api-keys",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        api_help_label.grid(row=4, column=0, columnspan=2, padx=10, pady=5)
        
        # Local Whisper settings frame
        self.local_frame = ctk.CTkFrame(section_frame)
        self.local_frame.grid(row=4, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        self.local_frame.grid_columnconfigure(1, weight=1)
        
        local_title = ctk.CTkLabel(
            self.local_frame,
            text="🖥️ Local Whisper Settings (Private & Free)",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        local_title.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        
        # Benefits explanation
        local_info = ctk.CTkLabel(
            self.local_frame,
            text="Benefits: Completely free, private (audio never leaves your computer), works offline\nSpeed: Slower than API but still quite fast on modern computers",
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        local_info.grid(row=1, column=0, columnspan=2, padx=10, pady=5)
        
        # Check local availability
        self.local_info = check_local_whisper_availability()
        
        # Local availability status
        availability_label = ctk.CTkLabel(self.local_frame, text="Availability:")
        availability_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        availability_status = "✅ Available" if self.local_info["available"] else "❌ Not installed"
        availability_color = "green" if self.local_info["available"] else "red"
        self.availability_status_label = ctk.CTkLabel(
            self.local_frame,
            text=availability_status,
            text_color=availability_color
        )
        self.availability_status_label.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        if self.local_info["available"]:
            # Model selection
            model_label = ctk.CTkLabel(self.local_frame, text="Model Size:")
            model_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")
            
            self.local_model_var = ctk.StringVar(value="base")
            self.local_model_dropdown = ctk.CTkOptionMenu(
                self.local_frame,
                variable=self.local_model_var,
                values=self.local_info["models"]
            )
            self.local_model_dropdown.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
            
            # Device selection
            device_label = ctk.CTkLabel(self.local_frame, text="Processing Device:")
            device_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")
            
            device_options = ["auto", "cpu"]
            if self.local_info["device_info"].get("cuda_available", False):
                device_options.append("cuda")
                
            self.device_var = ctk.StringVar(value="auto")
            self.device_dropdown = ctk.CTkOptionMenu(
                self.local_frame,
                variable=self.device_var,
                values=device_options
            )
            self.device_dropdown.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
            
            # System info
            if "device_info" in self.local_info:
                device_info = self.local_info["device_info"]
                info_text = f"CPU Cores: {device_info.get('cpu_cores', 'Unknown')}"
                if device_info.get('cuda_available'):
                    info_text += f" | CUDA GPUs: {device_info.get('cuda_count', 0)}"
                    
                info_label = ctk.CTkLabel(
                    self.local_frame,
                    text=info_text,
                    font=ctk.CTkFont(size=12)
                )
                info_label.grid(row=5, column=0, columnspan=2, padx=10, pady=5)
        else:
            # Installation instructions
            install_label = ctk.CTkLabel(
                self.local_frame,
                text="To use local Whisper, install: pip install whisper torch",
                font=ctk.CTkFont(size=12),
                text_color="orange"
            )
            install_label.grid(row=3, column=0, columnspan=2, padx=10, pady=10)
            
        # Language setting
        language_label = ctk.CTkLabel(section_frame, text="Default Language:")
        language_label.grid(row=5, column=0, padx=20, pady=5, sticky="w")
        
        self.language_var = ctk.StringVar(value="auto")
        language_options = ["auto", "en", "es", "fr", "de", "it", "pt", "zh", "ja", "ko"]
        self.language_dropdown = ctk.CTkOptionMenu(
            section_frame,
            variable=self.language_var,
            values=language_options
        )
        self.language_dropdown.grid(row=5, column=1, padx=20, pady=5, sticky="ew")
        
    def _create_cost_comparison_section(self):
        """Create cost comparison section."""
        row = 2
        
        # Get comparison data
        comparison = CostEstimator.get_service_comparison()
        
        # Section frame
        section_frame = ctk.CTkFrame(self.main_frame)
        section_frame.grid(row=row, column=0, sticky="ew", pady=10)
        section_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            section_frame,
            text="💰 Cost Comparison",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, padx=20, pady=15)
        
        # OpenAI column
        openai_frame = ctk.CTkFrame(section_frame)
        openai_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        openai_data = comparison["openai"]
        self._create_service_comparison_card(openai_frame, openai_data)
        
        # Local column
        local_frame = ctk.CTkFrame(section_frame)
        local_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        
        local_data = comparison["local"]
        self._create_service_comparison_card(local_frame, local_data)
        
    def _create_service_comparison_card(self, parent, service_data):
        """Create a comparison card for a service."""
        # Title
        title_label = ctk.CTkLabel(
            parent,
            text=service_data["name"],
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(padx=10, pady=10)
        
        # Cost info
        cost_frame = ctk.CTkFrame(parent)
        cost_frame.pack(padx=10, pady=5, fill="x")
        
        cost_per_min = f"${service_data['cost_per_minute']:.4f}/min"
        cost_per_hour = f"${service_data['cost_per_hour']:.2f}/hour"
        
        ctk.CTkLabel(cost_frame, text=f"Cost: {cost_per_min}").pack(pady=2)
        ctk.CTkLabel(cost_frame, text=f"({cost_per_hour})").pack(pady=2)
        
        # Pros
        pros_frame = ctk.CTkFrame(parent)
        pros_frame.pack(padx=10, pady=5, fill="x")
        
        ctk.CTkLabel(
            pros_frame,
            text="✅ Advantages:",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=5, pady=2)
        
        for pro in service_data["pros"][:3]:  # Show first 3
            ctk.CTkLabel(
                pros_frame,
                text=f"• {pro}",
                font=ctk.CTkFont(size=12)
            ).pack(anchor="w", padx=15, pady=1)
            
        # Cons
        cons_frame = ctk.CTkFrame(parent)
        cons_frame.pack(padx=10, pady=5, fill="x")
        
        ctk.CTkLabel(
            cons_frame,
            text="⚠️ Considerations:",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=5, pady=2)
        
        for con in service_data["cons"][:3]:  # Show first 3
            ctk.CTkLabel(
                cons_frame,
                text=f"• {con}",
                font=ctk.CTkFont(size=12)
            ).pack(anchor="w", padx=15, pady=1)
            
        # Quick stats
        stats_frame = ctk.CTkFrame(parent)
        stats_frame.pack(padx=10, pady=5, fill="x")
        
        stats = [
            f"Setup: {service_data['setup_difficulty']}",
            f"Speed: {service_data['processing_speed']}",
            f"Accuracy: {service_data['accuracy']}"
        ]
        
        for stat in stats:
            ctk.CTkLabel(
                stats_frame,
                text=stat,
                font=ctk.CTkFont(size=11)
            ).pack(anchor="w", padx=5, pady=1)
            
    def _create_summarization_section(self):
        """Create summarization settings section."""
        row = 3
        
        # Section frame
        section_frame = ctk.CTkFrame(self.main_frame)
        section_frame.grid(row=row, column=0, sticky="ew", pady=10)
        section_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            section_frame,
            text="📝 Summarization Settings",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=15)
        
        # Summary enable/disable
        enable_frame = ctk.CTkFrame(section_frame)
        enable_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.summarization_enabled_var = ctk.BooleanVar(value=True)
        self.summarization_checkbox = ctk.CTkCheckBox(
            enable_frame,
            text="Enable automatic summarization",
            variable=self.summarization_enabled_var,
            command=self._on_summarization_setting_changed,
            font=ctk.CTkFont(size=14)
        )
        self.summarization_checkbox.pack(padx=15, pady=15, anchor="w")
        
        # Cost information
        cost_info_frame = ctk.CTkFrame(section_frame)
        cost_info_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        # Cost explanation
        cost_title = ctk.CTkLabel(
            cost_info_frame,
            text="💰 Summary Cost Estimation",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        cost_title.pack(padx=15, pady=(15, 5), anchor="w")
        
        # Get sample cost estimates
        sample_costs = CostEstimator.estimate_summary_cost(10.0)  # 10 minute sample
        
        cost_details = [
            f"• Estimated cost: ~${sample_costs['per_minute']:.4f} per minute",
            f"• For 10 minutes: ~${sample_costs['total']:.3f}",
            f"• For 1 hour: ~${sample_costs['per_hour']:.2f}",
            "",
            "💡 Summary uses OpenAI GPT-3.5-turbo",
            "   Input: $0.0015/1K tokens, Output: $0.002/1K tokens",
            "   Estimated ~150 tokens/min input, ~200 tokens output"
        ]
        
        for detail in cost_details:
            ctk.CTkLabel(
                cost_info_frame,
                text=detail,
                font=ctk.CTkFont(size=12),
                text_color="gray" if detail.startswith("💡") or detail.startswith("   ") else None
            ).pack(padx=25, pady=1, anchor="w")
        
        # Recommendation
        recommendation_frame = ctk.CTkFrame(section_frame)
        recommendation_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(
            recommendation_frame,
            text="💡 Recommendation",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(padx=15, pady=(15, 5), anchor="w")
        
        ctk.CTkLabel(
            recommendation_frame,
            text="Summarization adds valuable insights with minimal cost.\nDisable only if you prefer manual review of full transcripts.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(padx=25, pady=(0, 15), anchor="w")
            
    def _create_ui_section(self):
        """Create UI settings section."""
        row = 4
        
        section_frame = ctk.CTkFrame(self.main_frame)
        section_frame.grid(row=row, column=0, sticky="ew", pady=10)
        section_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            section_frame,
            text="🎨 Interface Settings",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, padx=20, pady=15)
        
        # Theme selection
        theme_label = ctk.CTkLabel(section_frame, text="Theme:")
        theme_label.grid(row=1, column=0, padx=20, pady=5, sticky="w")
        
        self.theme_var = ctk.StringVar(value="dark")
        self.theme_dropdown = ctk.CTkOptionMenu(
            section_frame,
            variable=self.theme_var,
            values=["dark", "light", "system"]
        )
        self.theme_dropdown.grid(row=1, column=1, padx=20, pady=5, sticky="ew")
        
        # Auto-save setting
        self.auto_save_var = ctk.BooleanVar(value=True)
        self.auto_save_checkbox = ctk.CTkCheckBox(
            section_frame,
            text="Auto-save recordings to vault",
            variable=self.auto_save_var
        )
        self.auto_save_checkbox.grid(row=2, column=0, columnspan=2, padx=20, pady=10, sticky="w")
        
    def _create_action_buttons(self):
        """Create action buttons."""
        button_frame = ctk.CTkFrame(self.window)
        button_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        button_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Reset to defaults
        reset_button = ctk.CTkButton(
            button_frame,
            text="Reset to Defaults",
            command=self.reset_to_defaults,
            width=120
        )
        reset_button.grid(row=0, column=0, padx=5, pady=10)
        
        # Cancel
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.on_close,
            width=120
        )
        cancel_button.grid(row=0, column=1, padx=5, pady=10)
        
        # Save
        save_button = ctk.CTkButton(
            button_frame,
            text="Save Settings",
            command=self.save_settings,
            width=120
        )
        save_button.grid(row=0, column=2, padx=5, pady=10)
        
    def _on_service_changed(self, value):
        """Handle transcription service change."""
        # Auto-switch to local if OpenAI is selected but no API key
        if value == "openai" and not self.settings_manager.has_openai_api_key():
            # Show warning and switch back to local
            self.service_var.set("local")
            print("Warning: No OpenAI API key configured. Defaulting to local transcription.")
            
    def _on_api_key_changed(self, event=None):
        """Handle API key input changes."""
        api_key = self.api_key_var.get().strip()
        
        # Update status label
        if api_key and len(api_key) > 10 and api_key.startswith("sk-"):
            status_text = "✅ API Key entered"
            status_color = "green"
        elif api_key:
            status_text = "⚠️ Invalid format"
            status_color = "orange"
        else:
            status_text = "❌ Not configured"
            status_color = "red"
            
        self.api_key_status_label.configure(text=status_text, text_color=status_color)
        
    def _on_summarization_setting_changed(self):
        """Handle summarization setting changes."""
        # This callback could be expanded to show/hide cost details or provide warnings
        enabled = self.summarization_enabled_var.get()
        if not enabled:
            print("Info: Summarization disabled. Only transcripts will be saved.")
        else:
            print("Info: Summarization enabled. Transcripts will be automatically summarized.")
            
    def _toggle_api_key_visibility(self):
        """Toggle API key visibility between hidden and visible."""
        self.api_key_visible = not self.api_key_visible
        
        if self.api_key_visible:
            # Show the key
            self.api_key_entry.configure(show="")
            self.toggle_button.configure(text="🙈")  # Hide icon
        else:
            # Hide the key
            self.api_key_entry.configure(show="*")
            self.toggle_button.configure(text="👁️")  # Show icon
        
    def load_current_settings(self):
        """Load current settings into the UI."""
        settings = self.settings_manager.settings
        
        # Auto-default to local if no API key is configured
        service = settings.transcription.service
        if service == "openai" and not self.settings_manager.has_openai_api_key():
            service = "local"
            print("No OpenAI API key found. Defaulting to local transcription.")
        
        # Transcription settings
        self.service_var.set(service)
        self.language_var.set(settings.transcription.language)
        
        if hasattr(self, 'local_model_var'):
            self.local_model_var.set(settings.transcription.local_model)
        if hasattr(self, 'device_var'):
            self.device_var.set(settings.transcription.device)
            
        # UI settings
        self.theme_var.set(settings.ui.theme)
        self.auto_save_var.set(settings.ui.auto_save)
        
        # Summarization settings
        if hasattr(self, 'summarization_enabled_var'):
            self.summarization_enabled_var.set(settings.summarization.enabled)
        
        # API key
        if hasattr(self, 'api_key_var'):
            self.api_key_var.set(self.settings_manager.get_openai_api_key() or "")
        
    def save_settings(self):
        """Save current settings."""
        settings = self.settings_manager.settings
        
        # Update transcription settings
        settings.transcription.service = self.service_var.get()
        settings.transcription.language = self.language_var.get()
        
        if hasattr(self, 'local_model_var'):
            settings.transcription.local_model = self.local_model_var.get()
        if hasattr(self, 'device_var'):
            settings.transcription.device = self.device_var.get()
            
        # Update UI settings
        settings.ui.theme = self.theme_var.get()
        settings.ui.auto_save = self.auto_save_var.get()
        
        # Update summarization settings
        if hasattr(self, 'summarization_enabled_var'):
            settings.summarization.enabled = self.summarization_enabled_var.get()
        
        # Save API key to .env file
        if hasattr(self, 'api_key_var'):
            api_key = self.api_key_var.get().strip()
            self.settings_manager.save_openai_api_key(api_key)
        
        # Save to file
        self.settings_manager.save_settings()
        
        # Notify parent
        if self.on_settings_changed:
            self.on_settings_changed()
            
        # Close window
        self.on_close()
        
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        # Reset variables to defaults
        self.service_var.set("local")  # Default to local
        self.language_var.set("auto")
        self.theme_var.set("dark")
        self.auto_save_var.set(True)
        
        if hasattr(self, 'local_model_var'):
            self.local_model_var.set("base")
        if hasattr(self, 'device_var'):
            self.device_var.set("auto")
        if hasattr(self, 'api_key_var'):
            self.api_key_var.set("")  # Clear API key
            self._on_api_key_changed()  # Update status
            
    def on_close(self):
        """Handle window close."""
        self.window.grab_release()
        self.window.destroy()
