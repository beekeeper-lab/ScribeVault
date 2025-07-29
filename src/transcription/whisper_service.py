"""
Whisper transcription service for ScribeVault.
Supports both OpenAI API and local Whisper models.
"""

import openai
from pathlib import Path
from typing import Optional
import os
from dotenv import load_dotenv

# Try to import local whisper
try:
    import whisper
    LOCAL_WHISPER_AVAILABLE = True
except ImportError:
    LOCAL_WHISPER_AVAILABLE = False
    whisper = None

load_dotenv()

class WhisperService:
    """Handles audio transcription using OpenAI Whisper (API or local)."""
    
    def __init__(self, use_local: bool = False, local_model: str = "base", device: str = "auto"):
        """Initialize the Whisper service.
        
        Args:
            use_local: Whether to use local Whisper instead of API
            local_model: Local model size (tiny, base, small, medium, large)
            device: Device for local processing (auto, cpu, cuda)
        """
        self.use_local = use_local
        self.local_model_name = local_model
        self.device = device
        self.local_model = None
        
        if use_local:
            if not LOCAL_WHISPER_AVAILABLE:
                raise ImportError(
                    "Local Whisper not available. Install with: pip install whisper"
                )
            self._load_local_model()
        else:
            self.client = openai.OpenAI(
                api_key=os.getenv("OPENAI_API_KEY")
            )
            
    def _load_local_model(self):
        """Load the local Whisper model."""
        try:
            print(f"Loading local Whisper model: {self.local_model_name}")
            self.local_model = whisper.load_model(
                self.local_model_name, 
                device=self.device if self.device != "auto" else None
            )
            print("Local Whisper model loaded successfully")
        except Exception as e:
            print(f"Error loading local Whisper model: {e}")
            raise
        
    def transcribe_audio(self, audio_path: Path, language: str = None) -> Optional[str]:
        """Transcribe audio file to text.
        
        Args:
            audio_path: Path to the audio file
            language: Language code (e.g., 'en', 'es') or None for auto-detection
            
        Returns:
            Transcribed text or None if transcription failed
        """
        if self.use_local:
            return self._transcribe_local(audio_path, language)
        else:
            return self._transcribe_api(audio_path, language)
            
    def _transcribe_api(self, audio_path: Path, language: str = None) -> Optional[str]:
        """Transcribe using OpenAI API."""
        try:
            with open(audio_path, "rb") as audio_file:
                params = {
                    "model": "whisper-1",
                    "file": audio_file,
                    "response_format": "text"
                }
                
                if language:
                    params["language"] = language
                
                transcript = self.client.audio.transcriptions.create(**params)
            return transcript
            
        except Exception as e:
            print(f"API transcription error: {e}")
            return None
            
    def _transcribe_local(self, audio_path: Path, language: str = None) -> Optional[str]:
        """Transcribe using local Whisper model."""
        try:
            if not self.local_model:
                raise RuntimeError("Local model not loaded")
                
            print(f"Transcribing with local Whisper: {audio_path}")
            
            options = {}
            if language and language != "auto":
                options["language"] = language
                
            result = self.local_model.transcribe(str(audio_path), **options)
            
            return result["text"].strip()
            
        except Exception as e:
            print(f"Local transcription error: {e}")
            return None
            
    def transcribe_with_timestamps(self, audio_path: Path, language: str = None) -> Optional[dict]:
        """Transcribe audio with timestamp information.
        
        Args:
            audio_path: Path to the audio file
            language: Language code or None for auto-detection
            
        Returns:
            Transcription with timestamps or None if failed
        """
        if self.use_local:
            return self._transcribe_local_with_timestamps(audio_path, language)
        else:
            return self._transcribe_api_with_timestamps(audio_path, language)
            
    def _transcribe_api_with_timestamps(self, audio_path: Path, language: str = None) -> Optional[dict]:
        """Get timestamps using OpenAI API."""
        try:
            with open(audio_path, "rb") as audio_file:
                params = {
                    "model": "whisper-1",
                    "file": audio_file,
                    "response_format": "verbose_json",
                    "timestamp_granularities": ["word"]
                }
                
                if language:
                    params["language"] = language
                    
                transcript = self.client.audio.transcriptions.create(**params)
            return transcript
            
        except Exception as e:
            print(f"API timestamp transcription error: {e}")
            return None
            
    def _transcribe_local_with_timestamps(self, audio_path: Path, language: str = None) -> Optional[dict]:
        """Get timestamps using local Whisper model."""
        try:
            if not self.local_model:
                raise RuntimeError("Local model not loaded")
                
            options = {"word_timestamps": True}
            if language and language != "auto":
                options["language"] = language
                
            result = self.local_model.transcribe(str(audio_path), **options)
            
            return result
            
        except Exception as e:
            print(f"Local timestamp transcription error: {e}")
            return None
            
    def get_service_info(self) -> dict:
        """Get information about the current transcription service."""
        if self.use_local:
            return {
                "service": "local",
                "model": self.local_model_name,
                "device": self.device,
                "available": LOCAL_WHISPER_AVAILABLE,
                "loaded": self.local_model is not None
            }
        else:
            return {
                "service": "openai",
                "model": "whisper-1",
                "api_key_configured": bool(os.getenv("OPENAI_API_KEY")),
                "available": True
            }

def check_local_whisper_availability() -> dict:
    """Check if local Whisper is available and get system info.
    
    Returns:
        Dictionary with availability information
    """
    info = {
        "available": LOCAL_WHISPER_AVAILABLE,
        "error": None,
        "models": [],
        "device_info": {}
    }
    
    if LOCAL_WHISPER_AVAILABLE:
        try:
            # Available model sizes
            info["models"] = ["tiny", "base", "small", "medium", "large"]
            
            # Check for CUDA availability
            try:
                import torch
                info["device_info"] = {
                    "cuda_available": torch.cuda.is_available(),
                    "cuda_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
                    "cpu_cores": os.cpu_count()
                }
            except ImportError:
                info["device_info"] = {"cpu_cores": os.cpu_count()}
                
        except Exception as e:
            info["error"] = str(e)
    else:
        info["error"] = "Whisper package not installed"
        
    return info
