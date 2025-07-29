"""
Whisper transcription service for ScribeVault.
"""

import openai
from pathlib import Path
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class WhisperService:
    """Handles audio transcription using OpenAI Whisper."""
    
    def __init__(self):
        """Initialize the Whisper service."""
        self.client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
    def transcribe_audio(self, audio_path: Path) -> Optional[str]:
        """Transcribe audio file to text.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Transcribed text or None if transcription failed
        """
        try:
            with open(audio_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            return transcript
            
        except Exception as e:
            print(f"Transcription error: {e}")
            return None
            
    def transcribe_with_timestamps(self, audio_path: Path) -> Optional[dict]:
        """Transcribe audio with timestamp information.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Transcription with timestamps or None if failed
        """
        try:
            with open(audio_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["word"]
                )
            return transcript
            
        except Exception as e:
            print(f"Transcription error: {e}")
            return None
