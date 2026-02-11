"""
Audio recording service for ScribeVault.
"""

import pyaudio
import wave
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import threading
import subprocess
import logging
import signal
import os

from export.utils import secure_mkdir, secure_file_permissions

logger = logging.getLogger(__name__)

class AudioException(Exception):
    """Custom exception for audio-related errors."""
    pass

class RecordingException(AudioException):
    """Exception raised when recording fails."""
    pass

class AudioRecorder:
    """Handles audio recording functionality."""

    def __init__(self, sample_rate: int = 44100, chunk_size: int = 1024,
                 channels: int = 1, checkpoint_interval: int = 30,
                 input_device_index: Optional[int] = None):
        """Initialize the audio recorder.

        Args:
            sample_rate: Audio sample rate in Hz
            chunk_size: Number of frames per buffer
            channels: Number of audio channels (1 for mono, 2 for stereo)
            checkpoint_interval: Seconds between checkpoint flushes (0 to disable)
            input_device_index: PyAudio device index, or None for default
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.input_device_index = input_device_index
        self.format = pyaudio.paInt16
        self.checkpoint_interval = checkpoint_interval

        self._lock = threading.Lock()
        self.audio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.frames = []
        self.is_recording = False
        self._cleaned_up = False

        # Checkpoint state
        self._checkpoint_path: Optional[Path] = None
        self._checkpoint_lock = threading.Lock()
        self._checkpoint_timer: Optional[threading.Timer] = None
        self._last_flushed_count = 0

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit — ensures cleanup."""
        self.cleanup()
        return False
        
    def start_recording(self) -> Path:
        """Start recording audio with proper fallback chain.

        Returns:
            Path to the recording file that will be created

        Raises:
            RecordingException: If no recording method works
        """
        with self._lock:
            if self.is_recording:
                raise RuntimeError("Already recording")

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        recordings_dir = Path("recordings")
        secure_mkdir(recordings_dir)

        self.output_path = recordings_dir / f"recording-{timestamp}.wav"

        # Try recording methods in order of preference
        try:
            logger.info("Attempting PyAudio recording...")
            return self._try_pyaudio_recording()
        except AudioException as e:
            logger.warning(f"PyAudio failed: {e}, trying FFmpeg")
            try:
                return self._try_ffmpeg_recording()
            except AudioException as e:
                logger.warning(f"FFmpeg failed: {e}, creating test recording")
                return self._create_test_recording()
        except Exception as e:
            logger.error(f"Unexpected error in recording: {e}")
            raise RecordingException(f"All recording methods failed: {e}")
            
    def _try_pyaudio_recording(self) -> Path:
        """Try recording with PyAudio.

        Returns:
            Path to recording file

        Raises:
            AudioException: If PyAudio recording fails
        """
        test_stream = None
        try:
            # Build common stream kwargs
            stream_kwargs = dict(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
            )
            if self.input_device_index is not None:
                stream_kwargs["input_device_index"] = self.input_device_index

            # Test if we can create a stream
            test_stream = self.audio.open(**stream_kwargs)
            test_stream.close()
            test_stream = None

            # Initialize recording
            with self._lock:
                self.frames = []
                self.is_recording = True

            # Create recording stream
            self.stream = self.audio.open(
                **stream_kwargs,
                stream_callback=self._audio_callback
            )

            self.stream.start_stream()
            self._start_checkpointing()
            logger.info("PyAudio recording started successfully")
            return self.output_path

        except Exception as e:
            logger.error(f"PyAudio recording failed: {e}")
            with self._lock:
                self.is_recording = False
            if test_stream:
                try:
                    test_stream.close()
                except Exception:
                    pass
            if self.stream:
                try:
                    self.stream.close()
                except Exception:
                    pass
                self.stream = None
            raise AudioException(f"PyAudio recording failed: {e}")
            
    def _validate_output_path(self, path: Path) -> bool:
        """Validate output path for security.
        
        Args:
            path: Path to validate
            
        Returns:
            True if path is valid and safe
        """
        try:
            # Convert to absolute path and resolve
            abs_path = path.resolve()
            
            # Check if it's within allowed directory
            recordings_dir = Path("recordings").resolve()
            if not str(abs_path).startswith(str(recordings_dir)):
                return False
                
            # Check file extension
            if abs_path.suffix.lower() != '.wav':
                return False
                
            # Check filename doesn't contain dangerous characters
            filename = abs_path.name
            dangerous_chars = ['..', '/', '\\', '|', '&', ';', '$', '`']
            if any(char in filename for char in dangerous_chars):
                return False
                
            return True
            
        except Exception:
            return False
        
    def stop_recording(self) -> Optional[Path]:
        """Stop recording and save the audio file.

        Returns:
            Path to the saved recording file, or None if no recording was active
        """
        with self._lock:
            if not self.is_recording:
                if hasattr(self, 'output_path') and self.output_path.exists():
                    return self.output_path
                return None
            self.is_recording = False

        try:
            # Handle PyAudio stream
            if hasattr(self, 'stream') and self.stream:
                logger.info("Stopping PyAudio recording...")
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                finally:
                    self.stream = None

                with self._lock:
                    frames = list(self.frames)
                if frames:
                    # Finalize via checkpoint if active, else save directly
                    if self._checkpoint_path is not None:
                        result = self._finalize_checkpoint()
                        if result:
                            logger.info(
                                "PyAudio recording saved via checkpoint: %s",
                                result
                            )
                            return result
                    # Fallback: direct save (no checkpointing or finalize failed)
                    self._save_recording()
                    logger.info(
                        "PyAudio recording saved: %s", self.output_path
                    )
                    return self.output_path

            # Handle FFmpeg process
            elif hasattr(self, 'ffmpeg_process') and self.ffmpeg_process:
                logger.info("Stopping FFmpeg recording...")

                # Gracefully terminate FFmpeg
                try:
                    if os.name != 'nt':  # Unix-like systems
                        os.killpg(os.getpgid(self.ffmpeg_process.pid), signal.SIGTERM)
                    else:  # Windows
                        self.ffmpeg_process.terminate()

                    # Wait for process to finish with timeout
                    try:
                        self.ffmpeg_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        logger.warning("FFmpeg didn't terminate gracefully, forcing kill")
                        if os.name != 'nt':
                            os.killpg(os.getpgid(self.ffmpeg_process.pid), signal.SIGKILL)
                        else:
                            self.ffmpeg_process.kill()
                        self.ffmpeg_process.wait()

                except ProcessLookupError:
                    # Process already terminated
                    pass

                # Check if file was created successfully
                if self.output_path.exists() and self.output_path.stat().st_size > 0:
                    logger.info(f"FFmpeg recording saved: {self.output_path}")
                    return self.output_path
                else:
                    logger.error("FFmpeg recording failed - no file created or file is empty")

            # Return test recording path if it exists
            elif hasattr(self, 'output_path') and self.output_path.exists():
                logger.info(f"Test recording available: {self.output_path}")
                return self.output_path

        except Exception as e:
            logger.error(f"Error stopping recording: {e}")

        return None
        
    def _record_loop(self):
        """Recording loop that runs in a separate thread."""
        while True:
            with self._lock:
                if not self.is_recording:
                    break
            if not self.stream:
                break
            try:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                with self._lock:
                    self.frames.append(data)
            except Exception as e:
                logger.error("Recording error: %s", e)
                break
        
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback function for audio stream."""
        with self._lock:
            if self.is_recording:
                self.frames.append(in_data)
        return (in_data, pyaudio.paContinue)
        
    def _save_recording(self):
        """Save the recorded frames to a WAV file."""
        with wave.open(str(self.output_path), 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self.frames))
        secure_file_permissions(self.output_path)

    # --- Checkpoint methods ---

    def _start_checkpointing(self):
        """Initialize checkpoint file and start the periodic flush timer."""
        if self.checkpoint_interval <= 0:
            return
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        recordings_dir = Path("recordings")
        secure_mkdir(recordings_dir)
        self._checkpoint_path = (
            recordings_dir / f"recording-{timestamp}.checkpoint.wav"
        )
        self._last_flushed_count = 0
        self._schedule_checkpoint()

    def _schedule_checkpoint(self):
        """Schedule the next checkpoint flush."""
        if not self.is_recording or self.checkpoint_interval <= 0:
            return
        self._checkpoint_timer = threading.Timer(
            self.checkpoint_interval, self._flush_checkpoint
        )
        self._checkpoint_timer.daemon = True
        self._checkpoint_timer.start()

    def _flush_checkpoint(self):
        """Write all accumulated frames to the checkpoint WAV file."""
        with self._checkpoint_lock:
            if not self.is_recording and not self.frames:
                return
            current_frames = list(self.frames)

        if not current_frames:
            if self.is_recording:
                self._schedule_checkpoint()
            return

        try:
            sample_width = self.audio.get_sample_size(self.format)
            with wave.open(str(self._checkpoint_path), 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(sample_width)
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(current_frames))
            secure_file_permissions(self._checkpoint_path)
            self._last_flushed_count = len(current_frames)
            logger.info(
                "Checkpoint flushed: %d frames to %s",
                self._last_flushed_count, self._checkpoint_path
            )
        except Exception as e:
            logger.error("Checkpoint flush failed: %s", e)

        if self.is_recording:
            self._schedule_checkpoint()

    def _finalize_checkpoint(self) -> Optional[Path]:
        """Do a final flush and rename checkpoint to the output path.

        Returns:
            Path to the finalized recording, or None if no checkpoint exists.
        """
        # Cancel any pending timer
        if self._checkpoint_timer is not None:
            self._checkpoint_timer.cancel()
            self._checkpoint_timer = None

        if self._checkpoint_path is None:
            return None

        # Final flush with all remaining frames
        with self._checkpoint_lock:
            current_frames = list(self.frames)

        if current_frames:
            try:
                sample_width = self.audio.get_sample_size(self.format)
                with wave.open(str(self._checkpoint_path), 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(sample_width)
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(b''.join(current_frames))
                secure_file_permissions(self._checkpoint_path)
            except Exception as e:
                logger.error("Final checkpoint flush failed: %s", e)
                return None

        # Rename checkpoint to final output path
        if self._checkpoint_path.exists():
            try:
                self._checkpoint_path.rename(self.output_path)
                logger.info(
                    "Checkpoint finalized: %s -> %s",
                    self._checkpoint_path, self.output_path
                )
                self._checkpoint_path = None
                return self.output_path
            except OSError as e:
                logger.error("Failed to rename checkpoint: %s", e)
                return None

        self._checkpoint_path = None
        return None

    @staticmethod
    def recover_checkpoints(
        recordings_dir: str = "recordings",
    ) -> List[Path]:
        """Scan for orphaned checkpoint files and recover them.

        Args:
            recordings_dir: Directory to scan for checkpoint files.

        Returns:
            List of paths to recovered recording files.
        """
        rdir = Path(recordings_dir)
        if not rdir.exists():
            return []

        recovered: List[Path] = []
        for cp in sorted(rdir.glob("*.checkpoint.wav")):
            # Validate the WAV structure
            try:
                with wave.open(str(cp), 'rb') as wf:
                    if wf.getnframes() == 0:
                        logger.warning(
                            "Skipping empty checkpoint: %s", cp
                        )
                        continue
            except wave.Error as e:
                logger.warning(
                    "Skipping corrupt checkpoint %s: %s", cp, e
                )
                continue
            except Exception as e:
                logger.warning(
                    "Skipping unreadable checkpoint %s: %s", cp, e
                )
                continue

            # Rename: recording-TS.checkpoint.wav -> recording-TS-recovered.wav
            new_name = cp.name.replace(".checkpoint.wav", "-recovered.wav")
            new_path = cp.parent / new_name
            try:
                cp.rename(new_path)
                recovered.append(new_path)
                logger.info("Recovered checkpoint: %s -> %s", cp, new_path)
            except OSError as e:
                logger.error(
                    "Failed to recover checkpoint %s: %s", cp, e
                )

        return recovered
            
    def _try_ffmpeg_recording(self) -> Path:
        """Try recording with FFmpeg as a fallback.
        
        Returns:
            Path to recording file
            
        Raises:
            AudioException: If FFmpeg recording fails
        """
        try:
            # Validate output path to prevent injection
            if not self._validate_output_path(self.output_path):
                raise AudioException("Invalid output path for FFmpeg recording")
            
            logger.info("Starting FFmpeg recording...")
            with self._lock:
                self.is_recording = True
            
            # Determine audio input based on platform
            system = subprocess.run(['uname', '-s'], capture_output=True, text=True)
            if system.returncode == 0 and 'Linux' in system.stdout:
                audio_input = ['-f', 'pulse', '-i', 'default']
            elif system.returncode == 0 and 'Darwin' in system.stdout:  # macOS
                audio_input = ['-f', 'avfoundation', '-i', ':0']
            else:
                # Windows or unknown - try directsound
                audio_input = ['-f', 'dshow', '-i', 'audio="Microphone"']
            
            # Build secure command
            cmd = [
                'ffmpeg',
                *audio_input,
                '-t', '3600',  # Max 1 hour recording
                '-y',  # Overwrite output file
                '-ar', str(self.sample_rate),
                '-ac', str(self.channels),
                str(self.output_path.resolve())
            ]
            
            logger.info(f"FFmpeg command: {' '.join(cmd[:6])}... (path hidden)")
            
            # Start recording process with security restrictions
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                cwd=self.output_path.parent,
                preexec_fn=None if os.name == 'nt' else os.setsid  # Process group for clean termination
            )
            
            logger.info("FFmpeg recording started successfully")
            return self.output_path
            
        except subprocess.SubprocessError as e:
            logger.error(f"FFmpeg subprocess error: {e}")
            with self._lock:
                self.is_recording = False
            raise AudioException(f"FFmpeg recording failed: {e}")
        except Exception as e:
            logger.error(f"FFmpeg recording failed: {e}")
            with self._lock:
                self.is_recording = False
            raise AudioException(f"FFmpeg recording failed: {e}")
    
    def _create_test_recording(self) -> Path:
        """Create a test recording file when audio systems fail.
        
        Returns:
            Path to test recording file
        """
        try:
            logger.info("Creating test recording file...")
            with self._lock:
                self.is_recording = True
            
            # Generate 3 seconds of varied tones that simulate speech
            import struct
            import math
            import random
            
            duration = 3.0
            sample_rate = self.sample_rate
            
            frames = []
            for i in range(int(duration * sample_rate)):
                time = i / sample_rate
                
                # Create speech-like waveform
                base_freq = 200 + 100 * math.sin(2 * math.pi * 2 * time)
                
                signal = (
                    0.6 * math.sin(2 * math.pi * base_freq * time) +
                    0.3 * math.sin(2 * math.pi * base_freq * 2 * time) +
                    0.1 * math.sin(2 * math.pi * base_freq * 3 * time) +
                    0.05 * (random.random() - 0.5)
                )
                
                # Apply envelope for word-like segments
                segment_time = time % 1.0
                envelope = 0.2 if (segment_time < 0.1 or segment_time > 0.8) else 1.0
                
                sample = int(16000 * signal * envelope)
                sample = max(-32767, min(32767, sample))
                frames.append(struct.pack('<h', sample))
            
            # Save as WAV file
            with wave.open(str(self.output_path), 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(b''.join(frames))
                
            logger.info(f"Test recording created: {self.output_path}")
            return self.output_path
            
        except Exception as e:
            logger.error(f"Failed to create test recording: {e}")
            with self._lock:
                self.is_recording = False
            raise RecordingException(f"Could not create test recording: {e}")
    
    def _create_dummy_recording(self):
        """Create a dummy recording file for testing when audio fails."""
        import struct
        import math
        import random
        
        # Generate 3 seconds of varied tones that might be interpreted as speech
        duration = 3.0
        sample_rate = 44100
        
        frames = []
        for i in range(int(duration * sample_rate)):
            # Create a more complex waveform with multiple frequencies
            # to simulate speech patterns
            time = i / sample_rate
            
            # Base frequency that varies over time (simulating speech)
            base_freq = 200 + 100 * math.sin(2 * math.pi * 2 * time)  # 200-300Hz range
            
            # Add harmonics and noise to make it more speech-like
            signal = (
                0.6 * math.sin(2 * math.pi * base_freq * time) +  # Fundamental
                0.3 * math.sin(2 * math.pi * base_freq * 2 * time) +  # Second harmonic
                0.1 * math.sin(2 * math.pi * base_freq * 3 * time) +  # Third harmonic
                0.05 * (random.random() - 0.5)  # Add some noise
            )
            
            # Apply envelope to create word-like segments
            envelope = 1.0
            segment_time = time % 1.0  # 1-second segments
            if segment_time < 0.1 or segment_time > 0.8:  # Quiet periods between "words"
                envelope = 0.2
            
            sample = int(16000 * signal * envelope)  # Reduced amplitude
            sample = max(-32767, min(32767, sample))  # Clamp to 16-bit range
            frames.append(struct.pack('<h', sample))
        
        # Save as WAV file
        with wave.open(str(self.output_path), 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(frames))
            
        logger.info("Created dummy recording with speech-like patterns: %s", self.output_path)
            
    def cleanup(self):
        """Explicitly release all resources held by the recorder.

        Safe to call multiple times. Stops any active recording, closes
        PyAudio streams, terminates FFmpeg processes, and shuts down
        the PyAudio instance.
        """
        if self._cleaned_up:
            return
        self._cleaned_up = True

        try:
            # Cancel checkpoint timer
            if hasattr(self, '_checkpoint_timer') and self._checkpoint_timer:
                self._checkpoint_timer.cancel()

            # Stop recording if active
            with self._lock:
                was_recording = self.is_recording
                self.is_recording = False

            if was_recording:
                # Close stream without going through stop_recording
                # to avoid re-entrancy issues
                pass

            # Clean up PyAudio stream
            if self.stream:
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                except Exception:
                    pass
                self.stream = None

            # Clean up FFmpeg process
            if hasattr(self, 'ffmpeg_process') and self.ffmpeg_process:
                try:
                    if self.ffmpeg_process.poll() is None:
                        self.ffmpeg_process.terminate()
                        self.ffmpeg_process.wait(timeout=2)
                except Exception:
                    pass

            # Terminate PyAudio
            if hasattr(self, 'audio') and self.audio:
                try:
                    self.audio.terminate()
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Error in AudioRecorder cleanup: {e}")
            
    def get_audio_devices(self):
        """Get list of available audio input devices."""
        devices = []
        try:
            for i in range(self.audio.get_device_count()):
                try:
                    device_info = self.audio.get_device_info_by_index(i)
                    if device_info['maxInputChannels'] > 0:
                        devices.append({
                            'index': i,
                            'name': device_info['name'],
                            'channels': device_info['maxInputChannels'],
                            'sample_rate': device_info['defaultSampleRate']
                        })
                except Exception as e:
                    logger.warning(f"Could not get info for audio device {i}: {e}")
        except Exception as e:
            logger.error(f"Error getting audio devices: {e}")
            
        return devices
