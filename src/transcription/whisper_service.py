"""
Whisper transcription service for ScribeVault.
Supports both OpenAI API and local Whisper models.
"""

import openai
from pathlib import Path
from typing import Optional, Union, Dict, Any, List
import os
from dotenv import load_dotenv
import logging

from utils.retry import retry_on_transient_error, APIRetryError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranscriptionException(Exception):
    """Custom exception for transcription-related errors."""
    pass

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
    
    def __init__(self, settings_manager=None, use_local: bool = None, local_model: str = None, device: str = None):
        """Initialize the Whisper service.
        
        Args:
            settings_manager: Settings manager instance (preferred)
            use_local: Whether to use local Whisper instead of API (fallback)
            local_model: Local model size (fallback)
            device: Device for local processing (fallback)
        """
        if settings_manager:
            # Use settings manager (preferred approach)
            self.settings_manager = settings_manager
            settings = settings_manager.settings.transcription
            
            # Auto-default to local if OpenAI API key is missing/invalid
            if settings.service == "openai" and not settings_manager.has_openai_api_key():
                print("⚠️ OpenAI API key not configured. Defaulting to local transcription.")
                self.use_local = True
            else:
                self.use_local = settings.service == "local"
                
            self.local_model_name = settings.local_model
            self.device = settings.device
            self.language = settings.language
        else:
            # Fallback to direct parameters (backwards compatibility)
            self.settings_manager = None
            self.use_local = use_local if use_local is not None else False
            self.local_model_name = local_model or "base"
            self.device = device or "auto"
            self.language = "auto"
        
        self.local_model = None
        
        if self.use_local:
            if not LOCAL_WHISPER_AVAILABLE:
                raise ImportError(
                    "Local Whisper not available. Install with: pip install whisper"
                )
            self._load_local_model()
        else:
            # Check API key before creating client
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key or api_key.strip() == "":
                print("⚠️ No OpenAI API key found. Falling back to local transcription.")
                self.use_local = True
                if LOCAL_WHISPER_AVAILABLE:
                    self._load_local_model()
                else:
                    raise ValueError("No transcription method available: missing API key and local Whisper not installed")
            else:
                self.client = openai.OpenAI(api_key=api_key)
            
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
        # Use provided language or fall back to settings
        if language is None:
            language = getattr(self, 'language', 'auto')
            if language == 'auto':
                language = None
                
        if self.use_local:
            return self._transcribe_local(audio_path, language)
        else:
            return self._transcribe_api(audio_path, language)
            
    @retry_on_transient_error()
    def _call_transcription_api(self, audio_file, language: str = None,
                                response_format: str = "text",
                                timestamp_granularities=None):
        """Make a transcription API call with retry on transient errors."""
        params = {
            "model": "whisper-1",
            "file": audio_file,
            "response_format": response_format,
        }
        if language:
            params["language"] = language
        if timestamp_granularities:
            params["timestamp_granularities"] = timestamp_granularities
        return self.client.audio.transcriptions.create(**params)

    def _transcribe_api(self, audio_path: Path, language: str = None) -> Optional[str]:
        """Transcribe using OpenAI API."""
        try:
            logger.info(f"Starting API transcription for: {audio_path.name}")

            with open(audio_path, "rb") as audio_file:
                transcript = self._call_transcription_api(
                    audio_file, language=language, response_format="text"
                )

            logger.info("API transcription completed successfully")
            return transcript

        except APIRetryError as e:
            logger.error("API transcription failed after retries: %s", e)
            raise TranscriptionException(
                "Transcription failed after multiple retries. "
                "Please check your connection and try again."
            )
        except FileNotFoundError:
            logger.error(f"Audio file not found: {audio_path}")
            raise TranscriptionException(f"Audio file not found: {audio_path}")
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}", exc_info=True)
            raise TranscriptionException(f"API transcription failed: {e}")
        except Exception as e:
            logger.exception("Unexpected error in API transcription")
            raise TranscriptionException(f"Unexpected transcription error: {e}")
            
    def _transcribe_local(self, audio_path: Union[str, Path], language: str = None) -> Optional[str]:
        """Transcribe using local Whisper model."""
        try:
            if not self.local_model:
                raise TranscriptionException("Local model not loaded")
            
            # Ensure audio_path is a Path object
            if isinstance(audio_path, str):
                audio_path = Path(audio_path)
                
            logger.info(f"Starting local transcription for: {audio_path.name}")
            
            options = {}
            if language and language != "auto":
                options["language"] = language
                
            result = self.local_model.transcribe(str(audio_path), **options)
            
            logger.info("Local transcription completed successfully")
            return result["text"].strip()
            
        except Exception as e:
            logger.exception(f"Local transcription error for {audio_path}")
            raise TranscriptionException(f"Local transcription failed: {e}")
            
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
                transcript = self._call_transcription_api(
                    audio_file,
                    language=language,
                    response_format="verbose_json",
                    timestamp_granularities=["word"],
                )
            return transcript

        except APIRetryError as e:
            logger.error("Timestamp transcription failed after retries: %s", e)
            return None
        except Exception as e:
            logger.error("API timestamp transcription error: %s", e)
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
            
    def transcribe_with_diarization(
        self, audio_path: Path, language: str = None
    ) -> Dict[str, Any]:
        """Transcribe audio with speaker diarization.

        Gets word-level timestamps from Whisper, then runs diarization
        to identify speaker changes. Falls back to plain transcription
        if diarization fails or is disabled.

        Args:
            audio_path: Path to the audio file
            language: Language code or None for auto-detection

        Returns:
            Dict with keys:
              - 'transcription': raw transcription text
              - 'diarized_transcription': speaker-labeled text (or None)
        """
        # Get raw transcription
        transcription = self.transcribe_audio(audio_path, language)

        result = {
            "transcription": transcription,
            "diarized_transcription": None,
        }

        # Check if diarization is enabled via settings
        diarization_settings = None
        if self.settings_manager:
            diarization_settings = getattr(
                self.settings_manager.settings, "diarization", None
            )
            if diarization_settings and not diarization_settings.enabled:
                logger.info("Diarization is disabled in settings")
                return result

        # Try to get word-level timestamps for diarization
        try:
            timestamp_result = self.transcribe_with_timestamps(audio_path, language)
            word_timestamps = self._extract_word_timestamps(timestamp_result)
        except Exception as e:
            logger.warning(f"Could not get word timestamps for diarization: {e}")
            return result

        # Run diarization
        try:
            from transcription.diarization import DiarizationService, SCIPY_AVAILABLE

            if not SCIPY_AVAILABLE:
                logger.warning("scipy not available — skipping diarization")
                return result

            num_speakers = 0
            sensitivity = 0.5
            if diarization_settings:
                num_speakers = diarization_settings.num_speakers
                sensitivity = diarization_settings.sensitivity

            service = DiarizationService(
                num_speakers=num_speakers, sensitivity=sensitivity
            )
            diarization_result = service.diarize(audio_path, word_timestamps)

            if diarization_result and diarization_result.segments:
                result["diarized_transcription"] = (
                    diarization_result.to_labeled_text()
                )
                logger.info(
                    f"Diarization complete: {diarization_result.num_speakers} speakers detected"
                )
            else:
                logger.info("Diarization returned no segments — using plain transcription")

        except Exception as e:
            logger.warning(f"Diarization failed, falling back to plain transcription: {e}")

        return result

    def _extract_word_timestamps(
        self, timestamp_result
    ) -> Optional[List[Dict[str, Any]]]:
        """Extract word-level timestamps from a Whisper timestamp result.

        Handles both OpenAI API format and local Whisper format.

        Returns:
            List of dicts with 'word', 'start', 'end' keys, or None.
        """
        if timestamp_result is None:
            return None

        words = []

        # OpenAI API format: object with .words attribute
        if hasattr(timestamp_result, "words"):
            for w in timestamp_result.words:
                words.append({
                    "word": getattr(w, "word", str(w)),
                    "start": getattr(w, "start", 0),
                    "end": getattr(w, "end", 0),
                })
            return words if words else None

        # Local Whisper format: dict with 'segments' containing 'words'
        if isinstance(timestamp_result, dict):
            segments = timestamp_result.get("segments", [])
            for seg in segments:
                seg_words = seg.get("words", [])
                for w in seg_words:
                    words.append({
                        "word": w.get("word", ""),
                        "start": w.get("start", 0),
                        "end": w.get("end", 0),
                    })
            if words:
                return words

            # Fallback: use segment-level timestamps
            for seg in segments:
                words.append({
                    "word": seg.get("text", "").strip(),
                    "start": seg.get("start", 0),
                    "end": seg.get("end", 0),
                })
            return words if words else None

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
