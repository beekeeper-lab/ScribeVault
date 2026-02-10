"""
Configuration management for ScribeVault.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import keyring for secure storage
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    keyring = None

load_dotenv()

@dataclass
class TranscriptionSettings:
    """Transcription service configuration."""
    service: str = "local"  # "local" or "openai"
    openai_model: str = "whisper-1"
    local_model: str = "base"  # tiny, base, small, medium, large
    device: str = "auto"  # auto, cpu, cuda
    language: str = "auto"  # auto, en, es, fr, etc.
    
    def __post_init__(self):
        """Validate settings after initialization."""
        valid_services = ["local", "openai"]
        if self.service not in valid_services:
            raise ValueError(f"Invalid service: {self.service}. Must be one of {valid_services}")
            
        valid_models = ["tiny", "base", "small", "medium", "large"]
        if self.local_model not in valid_models:
            raise ValueError(f"Invalid local model: {self.local_model}. Must be one of {valid_models}")
            
        valid_devices = ["auto", "cpu", "cuda"]
        if self.device not in valid_devices:
            raise ValueError(f"Invalid device: {self.device}. Must be one of {valid_devices}")

@dataclass
class SummarizationSettings:
    """Summarization service configuration."""
    enabled: bool = True
    service: str = "openai"
    model: str = "gpt-3.5-turbo"
    style: str = "concise"  # concise, detailed, bullet_points
    max_tokens: int = 500
    
    def __post_init__(self):
        """Validate settings after initialization."""
        valid_styles = ["concise", "detailed", "bullet_points"]
        if self.style not in valid_styles:
            raise ValueError(f"Invalid style: {self.style}. Must be one of {valid_styles}")
            
        if self.max_tokens < 1 or self.max_tokens > 4000:
            raise ValueError(f"Invalid max_tokens: {self.max_tokens}. Must be between 1 and 4000")

@dataclass
class UISettings:
    """User interface configuration."""
    theme: str = "dark"
    window_width: int = 1200
    window_height: int = 800
    auto_save: bool = True
    
    def __post_init__(self):
        """Validate settings after initialization."""
        valid_themes = ["dark", "light", "system"]
        if self.theme not in valid_themes:
            raise ValueError(f"Invalid theme: {self.theme}. Must be one of {valid_themes}")
            
        if self.window_width < 800 or self.window_width > 3840:
            raise ValueError(f"Invalid window_width: {self.window_width}. Must be between 800 and 3840")
            
        if self.window_height < 600 or self.window_height > 2160:
            raise ValueError(f"Invalid window_height: {self.window_height}. Must be between 600 and 2160")

@dataclass
class RecordingSettings:
    """Recording configuration."""
    checkpoint_interval_seconds: int = 30

    def __post_init__(self):
        """Validate settings after initialization."""
        if self.checkpoint_interval_seconds < 10 or self.checkpoint_interval_seconds > 300:
            raise ValueError(
                f"Invalid checkpoint_interval_seconds: {self.checkpoint_interval_seconds}. "
                "Must be between 10 and 300"
            )

@dataclass
class AppSettings:
    """Main application settings."""
    transcription: TranscriptionSettings
    summarization: SummarizationSettings
    ui: UISettings
    recording: RecordingSettings = None
    recordings_dir: str = "recordings"
    vault_dir: str = "vault"

    def __post_init__(self):
        if self.recording is None:
            self.recording = RecordingSettings()

class SettingsManager:
    """Manages application settings and configuration."""
    
    def __init__(self, config_file: str = "config/settings.json"):
        """Initialize settings manager.
        
        Args:
            config_file: Path to the configuration file
        """
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(exist_ok=True)
        
        # Load settings or create defaults
        self.settings = self._load_settings()
        
    def _load_settings(self) -> AppSettings:
        """Load settings from file or create defaults."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    
                return AppSettings(
                    transcription=TranscriptionSettings(**data.get('transcription', {})),
                    summarization=SummarizationSettings(**data.get('summarization', {})),
                    ui=UISettings(**data.get('ui', {})),
                    recording=RecordingSettings(**data.get('recording', {})),
                    recordings_dir=data.get('recordings_dir', 'recordings'),
                    vault_dir=data.get('vault_dir', 'vault')
                )
            except Exception as e:
                print(f"Error loading settings: {e}")
                
        # Return defaults if file doesn't exist or failed to load
        return AppSettings(
            transcription=TranscriptionSettings(),
            summarization=SummarizationSettings(),
            ui=UISettings(),
            recording=RecordingSettings()
        )
        
    def save_settings(self):
        """Save current settings to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(asdict(self.settings), f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
            
    def get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key from secure storage or environment."""
        # Try keyring first (secure)
        if KEYRING_AVAILABLE:
            try:
                key = keyring.get_password("ScribeVault", "openai_api_key")
                if key:
                    return key
            except Exception as e:
                logger.warning(f"Could not access keyring: {e}")
        
        # Fallback to environment variable
        return os.getenv("OPENAI_API_KEY")
        
    def has_openai_api_key(self) -> bool:
        """Check if OpenAI API key is configured."""
        key = self.get_openai_api_key()
        return key is not None and key.strip() != "" and key != "your-openai-api-key-here"
        
    def save_openai_api_key(self, api_key: str):
        """Save OpenAI API key securely.
        
        Args:
            api_key: The OpenAI API key to save
        """
        # Try to save to keyring first (secure)
        if KEYRING_AVAILABLE:
            try:
                if api_key.strip():
                    keyring.set_password("ScribeVault", "openai_api_key", api_key.strip())
                    logger.info("API key saved securely to system keyring")
                else:
                    keyring.delete_password("ScribeVault", "openai_api_key")
                    logger.info("API key removed from system keyring")
                
                # Also update .env for compatibility
                self._update_env_file(api_key)
                return
                
            except Exception as e:
                logger.warning(f"Could not save to keyring: {e}, falling back to .env file")
        
        # Fallback to .env file with warning
        logger.warning("Saving API key to .env file (less secure). Install 'keyring' package for secure storage.")
        self._update_env_file(api_key)
        
    def _update_env_file(self, api_key: str):
        """Update .env file with API key (fallback method).
        
        Args:
            api_key: The API key to save
        """
        env_file = Path(".env")
        
        # Read existing .env content
        env_content = {}
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_content[key.strip()] = value.strip()
        
        # Update API key
        if api_key.strip():
            env_content['OPENAI_API_KEY'] = api_key.strip()
        elif 'OPENAI_API_KEY' in env_content:
            # Remove key if empty
            del env_content['OPENAI_API_KEY']
        
        # Write back to .env file securely
        try:
            # Create with restricted permissions
            env_file.touch(mode=0o600, exist_ok=True)
            
            with open(env_file, 'w') as f:
                for key, value in env_content.items():
                    f.write(f"{key}={value}\n")
            
            # Ensure file has restricted permissions
            env_file.chmod(0o600)
            
            # Reload environment variables
            load_dotenv(override=True)
            logger.info(f"API key {'saved' if api_key.strip() else 'removed'} in .env file")
            
        except Exception as e:
            logger.error(f"Error saving API key to .env file: {e}")
            raise
            
    def validate_openai_api_key(self, api_key: str) -> bool:
        """Validate OpenAI API key format.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            True if the key format is valid
        """
        if not api_key or not isinstance(api_key, str):
            return False
            
        api_key = api_key.strip()
        
        # Basic format validation
        if not api_key.startswith("sk-"):
            return False
            
        if len(api_key) < 20:  # OpenAI keys are much longer
            return False
            
        return True

class CostEstimator:
    """Provides cost estimates for different transcription services."""
    
    # OpenAI Whisper API pricing (per minute)
    OPENAI_WHISPER_COST_PER_MINUTE = 0.006
    
    # OpenAI GPT-3.5-turbo pricing (per 1K tokens)
    # Input: $0.0015/1K tokens, Output: $0.002/1K tokens
    OPENAI_GPT_INPUT_COST_PER_1K_TOKENS = 0.0015
    OPENAI_GPT_OUTPUT_COST_PER_1K_TOKENS = 0.002
    
    # Estimated tokens for typical transcripts and summaries
    TOKENS_PER_MINUTE_TRANSCRIPT = 150  # ~150 tokens per minute of speech
    TOKENS_PER_SUMMARY = 200  # Average summary output tokens
    
    # Local processing costs (electricity, hardware wear)
    LOCAL_PROCESSING_COST_PER_MINUTE = 0.0  # Completely free
    
    @classmethod
    def estimate_openai_cost(cls, minutes: float, include_summary: bool = True) -> Dict[str, float]:
        """Estimate OpenAI API costs.
        
        Args:
            minutes: Duration in minutes
            include_summary: Whether to include summarization costs
            
        Returns:
            Cost breakdown dictionary
        """
        transcription_cost = minutes * cls.OPENAI_WHISPER_COST_PER_MINUTE
        
        if include_summary:
            # Estimate summary costs
            input_tokens = minutes * cls.TOKENS_PER_MINUTE_TRANSCRIPT
            output_tokens = cls.TOKENS_PER_SUMMARY
            
            summary_cost = (
                (input_tokens / 1000) * cls.OPENAI_GPT_INPUT_COST_PER_1K_TOKENS +
                (output_tokens / 1000) * cls.OPENAI_GPT_OUTPUT_COST_PER_1K_TOKENS
            )
        else:
            summary_cost = 0.0
        
        total_cost = transcription_cost + summary_cost
        
        return {
            "transcription": transcription_cost,
            "summary": summary_cost,
            "total": total_cost,
            "per_minute": total_cost / minutes if minutes > 0 else 0,
            "per_hour": total_cost * 60 / minutes if minutes > 0 else 0
        }
        
    @classmethod
    def estimate_local_cost(cls, minutes: float, include_summary: bool = True) -> Dict[str, float]:
        """Estimate local processing costs.
        
        Args:
            minutes: Duration in minutes
            include_summary: Whether to include summarization costs (still requires OpenAI for now)
            
        Returns:
            Cost breakdown dictionary
        """
        processing_cost = minutes * cls.LOCAL_PROCESSING_COST_PER_MINUTE
        
        if include_summary:
            # Summary still requires OpenAI API
            input_tokens = minutes * cls.TOKENS_PER_MINUTE_TRANSCRIPT
            output_tokens = cls.TOKENS_PER_SUMMARY
            
            summary_cost = (
                (input_tokens / 1000) * cls.OPENAI_GPT_INPUT_COST_PER_1K_TOKENS +
                (output_tokens / 1000) * cls.OPENAI_GPT_OUTPUT_COST_PER_1K_TOKENS
            )
        else:
            summary_cost = 0.0
        
        total_cost = processing_cost + summary_cost
        
        return {
            "transcription": processing_cost,
            "summary": summary_cost,
            "total": total_cost,
            "per_minute": total_cost / minutes if minutes > 0 else 0,
            "per_hour": total_cost * 60 / minutes if minutes > 0 else 0
        }
        
    @classmethod
    def estimate_summary_cost(cls, minutes: float) -> Dict[str, float]:
        """Estimate just the summarization costs.
        
        Args:
            minutes: Duration in minutes of audio/transcript
            
        Returns:
            Summary cost breakdown dictionary
        """
        input_tokens = minutes * cls.TOKENS_PER_MINUTE_TRANSCRIPT
        output_tokens = cls.TOKENS_PER_SUMMARY
        
        input_cost = (input_tokens / 1000) * cls.OPENAI_GPT_INPUT_COST_PER_1K_TOKENS
        output_cost = (output_tokens / 1000) * cls.OPENAI_GPT_OUTPUT_COST_PER_1K_TOKENS
        total_cost = input_cost + output_cost
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total": total_cost,
            "per_minute": total_cost / minutes if minutes > 0 else 0,
            "per_hour": total_cost * 60 / minutes if minutes > 0 else 0
        }
        
    @classmethod
    def get_service_comparison(cls) -> Dict[str, Any]:
        """Get comparison between transcription services.
        
        Returns:
            Comparison data for UI display
        """
        return {
            "openai": {
                "name": "OpenAI Whisper API",
                "cost_per_minute": cls.OPENAI_WHISPER_COST_PER_MINUTE,
                "cost_per_hour": cls.OPENAI_WHISPER_COST_PER_MINUTE * 60,
                "pros": [
                    "High accuracy",
                    "Fast processing",
                    "No local setup required",
                    "Supports many languages",
                    "Automatic language detection"
                ],
                "cons": [
                    "Requires internet connection",
                    "Usage costs apply",
                    "Requires API key",
                    "Audio data sent to OpenAI"
                ],
                "setup_difficulty": "Easy",
                "processing_speed": "Fast",
                "accuracy": "Excellent"
            },
            "local": {
                "name": "Local Whisper",
                "cost_per_minute": cls.LOCAL_PROCESSING_COST_PER_MINUTE,
                "cost_per_hour": cls.LOCAL_PROCESSING_COST_PER_MINUTE * 60,
                "pros": [
                    "No usage costs",
                    "Complete privacy (offline)",
                    "No internet required",
                    "No API key needed",
                    "Multiple model sizes available"
                ],
                "cons": [
                    "Requires local setup",
                    "Uses computer resources",
                    "Slower on older hardware",
                    "Large model downloads",
                    "Requires Python packages"
                ],
                "setup_difficulty": "Medium",
                "processing_speed": "Variable (depends on hardware)",
                "accuracy": "Excellent (same models as API)"
            }
        }
        
    @classmethod
    def get_cost_comparison(cls, minutes: float, include_summary: bool = True) -> Dict[str, Dict[str, float]]:
        """Get dynamic cost comparison between OpenAI API and local processing.
        
        Args:
            minutes: Duration in minutes
            include_summary: Whether to include summarization costs
            
        Returns:
            Dictionary with 'openai' and 'local' cost breakdowns
        """
        openai_costs = cls.estimate_openai_cost(minutes, include_summary)
        local_costs = cls.estimate_local_cost(minutes, include_summary)
        
        # Calculate savings
        total_savings = openai_costs["total"] - local_costs["total"]
        percent_savings = (total_savings / openai_costs["total"] * 100) if openai_costs["total"] > 0 else 0
        
        return {
            "openai": openai_costs,
            "local": local_costs,
            "savings": {
                "amount": total_savings,
                "percentage": percent_savings
            }
        }
