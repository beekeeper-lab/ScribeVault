"""
Speaker diarization service for ScribeVault.
Detects speaker changes and assigns speaker labels to transcription segments.

Uses audio feature extraction with spectral clustering to identify
different speakers in a conversation.
"""

import wave
import math
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any

import numpy as np

logger = logging.getLogger(__name__)

# Try to import scipy for clustering
try:
    from scipy.cluster.hierarchy import fcluster, linkage
    from scipy.spatial.distance import pdist
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("scipy not available — speaker diarization will be disabled")


@dataclass
class DiarizedSegment:
    """A segment of transcription with speaker label."""
    speaker: str
    text: str
    start: float
    end: float


@dataclass
class DiarizationResult:
    """Result of speaker diarization."""
    segments: List[DiarizedSegment] = field(default_factory=list)
    num_speakers: int = 0

    def to_labeled_text(self) -> str:
        """Format diarized segments as labeled text.

        Returns:
            Formatted string like "Speaker 1: text\\nSpeaker 2: text\\n..."
        """
        if not self.segments:
            return ""

        lines = []
        current_speaker = None
        current_text_parts = []

        for segment in self.segments:
            if segment.speaker != current_speaker:
                if current_speaker is not None:
                    lines.append(f"{current_speaker}: {' '.join(current_text_parts)}")
                current_speaker = segment.speaker
                current_text_parts = [segment.text]
            else:
                current_text_parts.append(segment.text)

        # Flush the last speaker
        if current_speaker is not None:
            lines.append(f"{current_speaker}: {' '.join(current_text_parts)}")

        return "\n\n".join(lines)


class DiarizationService:
    """Handles speaker diarization using audio feature extraction and clustering."""

    # Audio analysis parameters
    FRAME_DURATION_MS = 30  # Duration of each analysis frame in ms
    ENERGY_THRESHOLD = 0.01  # Minimum energy to consider a frame voiced
    MIN_SEGMENT_DURATION = 0.5  # Minimum segment duration in seconds
    NUM_MFCC_FEATURES = 13  # Number of MFCC-like features to extract
    EMBEDDING_WINDOW_SEC = 1.5  # Window size for speaker embeddings

    def __init__(self, num_speakers: int = 0, sensitivity: float = 0.5):
        """Initialize the diarization service.

        Args:
            num_speakers: Expected number of speakers (0 = auto-detect, max 6)
            sensitivity: Speaker change sensitivity (0.0-1.0, higher = more splits)
        """
        if not SCIPY_AVAILABLE:
            logger.warning("DiarizationService created but scipy is not available")

        self.num_speakers = min(num_speakers, 6)
        self.sensitivity = max(0.0, min(1.0, sensitivity))

    def diarize(
        self, audio_path: Path, word_timestamps: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[DiarizationResult]:
        """Perform speaker diarization on an audio file.

        Args:
            audio_path: Path to the WAV audio file
            word_timestamps: Optional list of word-level timestamps from Whisper.
                Each entry should have 'word', 'start', 'end' keys.

        Returns:
            DiarizationResult with speaker-labeled segments, or None on failure
        """
        if not SCIPY_AVAILABLE:
            logger.error("Cannot diarize: scipy is not installed")
            return None

        try:
            audio_path = Path(audio_path)
            if not audio_path.exists():
                logger.error(f"Audio file not found: {audio_path}")
                return None

            # Read audio data
            samples, sample_rate = self._read_wav(audio_path)
            if samples is None or len(samples) == 0:
                logger.error("Failed to read audio data")
                return None

            # If no word timestamps provided, create uniform segments
            if not word_timestamps:
                word_timestamps = self._create_uniform_segments(
                    len(samples) / sample_rate
                )

            # Extract speaker embeddings for each segment window
            embeddings, segment_groups = self._extract_embeddings(
                samples, sample_rate, word_timestamps
            )

            if len(embeddings) < 2:
                # Only one segment or not enough data — single speaker
                return self._single_speaker_result(word_timestamps)

            # Cluster embeddings to identify speakers
            labels = self._cluster_speakers(embeddings)
            if labels is None:
                return self._single_speaker_result(word_timestamps)

            # Map cluster labels to speaker labels
            num_speakers = len(set(labels))

            # Build diarized segments
            segments = self._build_segments(
                word_timestamps, segment_groups, labels
            )

            return DiarizationResult(
                segments=segments, num_speakers=num_speakers
            )

        except Exception as e:
            logger.exception(f"Diarization failed: {e}")
            return None

    def _read_wav(self, audio_path: Path):
        """Read WAV file and return mono samples as numpy array.

        Returns:
            Tuple of (samples_array, sample_rate) or (None, None) on failure.
        """
        try:
            with wave.open(str(audio_path), "rb") as wf:
                n_channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                sample_rate = wf.getframerate()
                n_frames = wf.getnframes()

                raw_data = wf.readframes(n_frames)

            # Convert to numpy array
            if sample_width == 2:
                dtype = np.int16
            elif sample_width == 4:
                dtype = np.int32
            elif sample_width == 1:
                dtype = np.uint8
            else:
                logger.error(f"Unsupported sample width: {sample_width}")
                return None, None

            samples = np.frombuffer(raw_data, dtype=dtype).astype(np.float32)

            # Convert to mono if stereo
            if n_channels > 1:
                samples = samples.reshape(-1, n_channels).mean(axis=1)

            # Normalize to [-1, 1]
            max_val = np.iinfo(dtype).max if dtype != np.float32 else 1.0
            samples = samples / max_val

            return samples, sample_rate

        except Exception as e:
            logger.error(f"Failed to read WAV file: {e}")
            return None, None

    def _create_uniform_segments(self, duration: float):
        """Create uniform time segments when no word timestamps are available."""
        segment_duration = 2.0  # seconds per segment
        segments = []
        t = 0.0
        while t < duration:
            end = min(t + segment_duration, duration)
            segments.append({
                "word": f"[segment {len(segments)}]",
                "start": t,
                "end": end,
            })
            t = end
        return segments

    def _extract_embeddings(self, samples, sample_rate, word_timestamps):
        """Extract speaker embeddings for windows of words.

        Groups consecutive words into windows and extracts audio features
        for each window.

        Returns:
            Tuple of (embeddings_array, segment_groups) where segment_groups
            maps each embedding index to the word indices it covers.
        """
        embeddings = []
        segment_groups = []

        window_sec = self.EMBEDDING_WINDOW_SEC
        current_group = []
        group_start = None

        for i, wt in enumerate(word_timestamps):
            start = wt.get("start", 0)
            end = wt.get("end", start + 0.5)

            if group_start is None:
                group_start = start

            current_group.append(i)

            # When window is full or this is the last word
            if (end - group_start >= window_sec) or i == len(word_timestamps) - 1:
                group_end = end

                # Extract audio for this window
                start_sample = int(group_start * sample_rate)
                end_sample = int(group_end * sample_rate)
                start_sample = max(0, min(start_sample, len(samples)))
                end_sample = max(start_sample, min(end_sample, len(samples)))

                audio_chunk = samples[start_sample:end_sample]

                if len(audio_chunk) > 0:
                    embedding = self._compute_embedding(audio_chunk, sample_rate)
                    if embedding is not None:
                        embeddings.append(embedding)
                        segment_groups.append(list(current_group))

                current_group = []
                group_start = None

        if len(embeddings) == 0:
            return np.array([]), []

        return np.array(embeddings), segment_groups

    def _compute_embedding(self, audio_chunk, sample_rate):
        """Compute a speaker embedding vector from an audio chunk.

        Extracts MFCC-like features using a simple filterbank approach.
        """
        try:
            if len(audio_chunk) < sample_rate * 0.1:
                # Too short — pad or skip
                if len(audio_chunk) == 0:
                    return None
                audio_chunk = np.pad(
                    audio_chunk,
                    (0, max(0, int(sample_rate * 0.1) - len(audio_chunk))),
                )

            # Frame the signal
            frame_length = int(sample_rate * 0.025)  # 25ms frames
            frame_step = int(sample_rate * 0.010)  # 10ms step
            num_frames = max(
                1, (len(audio_chunk) - frame_length) // frame_step + 1
            )

            # Pre-emphasis
            emphasized = np.append(
                audio_chunk[0], audio_chunk[1:] - 0.97 * audio_chunk[:-1]
            )

            # Windowing and FFT
            features = []
            for frame_idx in range(num_frames):
                start = frame_idx * frame_step
                frame = emphasized[start:start + frame_length]
                if len(frame) < frame_length:
                    frame = np.pad(frame, (0, frame_length - len(frame)))

                # Apply Hamming window
                window = np.hamming(frame_length)
                windowed = frame * window

                # FFT
                fft_result = np.fft.rfft(windowed)
                power_spectrum = np.abs(fft_result) ** 2

                # Mel filterbank (simplified)
                n_filters = self.NUM_MFCC_FEATURES
                mel_features = self._apply_mel_filterbank(
                    power_spectrum, sample_rate, n_filters
                )
                features.append(mel_features)

            if not features:
                return None

            features = np.array(features)

            # Compute mean and std across frames as the embedding
            mean_features = np.mean(features, axis=0)
            std_features = np.std(features, axis=0)
            embedding = np.concatenate([mean_features, std_features])

            return embedding

        except Exception as e:
            logger.debug(f"Embedding computation failed: {e}")
            return None

    def _apply_mel_filterbank(self, power_spectrum, sample_rate, n_filters):
        """Apply a simple mel-scale filterbank to a power spectrum."""
        n_fft = (len(power_spectrum) - 1) * 2

        # Mel scale conversion
        def hz_to_mel(hz):
            return 2595 * math.log10(1 + hz / 700)

        def mel_to_hz(mel):
            return 700 * (10 ** (mel / 2595) - 1)

        low_mel = hz_to_mel(80)
        high_mel = hz_to_mel(sample_rate / 2)

        mel_points = np.linspace(low_mel, high_mel, n_filters + 2)
        hz_points = np.array([mel_to_hz(m) for m in mel_points])
        bin_points = np.floor((n_fft + 1) * hz_points / sample_rate).astype(int)
        bin_points = np.clip(bin_points, 0, len(power_spectrum) - 1)

        filterbank_energies = np.zeros(n_filters)
        for i in range(n_filters):
            left = bin_points[i]
            center = bin_points[i + 1]
            right = bin_points[i + 2]

            # Rising slope
            for j in range(left, center):
                if center > left and j < len(power_spectrum):
                    filterbank_energies[i] += (
                        power_spectrum[j] * (j - left) / (center - left)
                    )
            # Falling slope
            for j in range(center, right):
                if right > center and j < len(power_spectrum):
                    filterbank_energies[i] += (
                        power_spectrum[j] * (right - j) / (right - center)
                    )

        # Log compression
        filterbank_energies = np.where(
            filterbank_energies > 0,
            np.log(filterbank_energies),
            -10.0,
        )

        return filterbank_energies

    def _cluster_speakers(self, embeddings):
        """Cluster speaker embeddings using agglomerative clustering.

        Returns:
            Array of cluster labels (0-indexed), or None on failure.
        """
        try:
            n_samples = len(embeddings)
            if n_samples < 2:
                return None

            # Compute linkage
            distances = pdist(embeddings, metric="cosine")
            # Replace NaN distances with large value
            distances = np.nan_to_num(distances, nan=1.0)
            Z = linkage(distances, method="ward")

            if self.num_speakers > 0:
                # Use specified number of speakers
                n_clusters = min(self.num_speakers, n_samples)
            else:
                # Auto-detect: use distance threshold based on sensitivity
                # Lower sensitivity = fewer clusters (merge more)
                # Higher sensitivity = more clusters (split more)
                max_dist = Z[-1, 2] if len(Z) > 0 else 1.0
                threshold = max_dist * (1.0 - self.sensitivity * 0.7)
                labels = fcluster(Z, t=threshold, criterion="distance")

                n_clusters = len(set(labels))
                # Cap at reasonable range
                n_clusters = max(1, min(n_clusters, 6))

            labels = fcluster(Z, t=n_clusters, criterion="maxclust")

            return labels

        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            return None

    def _build_segments(self, word_timestamps, segment_groups, labels):
        """Build DiarizedSegment list from clustering results."""
        # Map each word index to a speaker label
        word_speakers = {}
        for group_idx, word_indices in enumerate(segment_groups):
            if group_idx < len(labels):
                speaker_num = labels[group_idx]
                for word_idx in word_indices:
                    word_speakers[word_idx] = f"Speaker {speaker_num}"

        # Build segments by merging consecutive words from same speaker
        segments = []
        current_speaker = None
        current_words = []
        current_start = 0.0
        current_end = 0.0

        for i, wt in enumerate(word_timestamps):
            speaker = word_speakers.get(i, "Speaker 1")
            word = wt.get("word", "").strip()
            start = wt.get("start", 0)
            end = wt.get("end", start)

            if speaker != current_speaker:
                # Speaker changed — flush current segment
                if current_speaker is not None and current_words:
                    segments.append(
                        DiarizedSegment(
                            speaker=current_speaker,
                            text=" ".join(current_words),
                            start=current_start,
                            end=current_end,
                        )
                    )
                current_speaker = speaker
                current_words = [word] if word else []
                current_start = start
                current_end = end
            else:
                if word:
                    current_words.append(word)
                current_end = end

        # Flush last segment
        if current_speaker is not None and current_words:
            segments.append(
                DiarizedSegment(
                    speaker=current_speaker,
                    text=" ".join(current_words),
                    start=current_start,
                    end=current_end,
                )
            )

        return segments

    def _single_speaker_result(self, word_timestamps):
        """Create a single-speaker result from word timestamps."""
        if not word_timestamps:
            return DiarizationResult(segments=[], num_speakers=1)

        text = " ".join(
            wt.get("word", "").strip()
            for wt in word_timestamps
            if wt.get("word", "").strip()
        )
        start = word_timestamps[0].get("start", 0)
        end = word_timestamps[-1].get("end", start)

        segment = DiarizedSegment(
            speaker="Speaker 1", text=text, start=start, end=end
        )
        return DiarizationResult(segments=[segment], num_speakers=1)
