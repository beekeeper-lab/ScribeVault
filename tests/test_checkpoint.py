"""
Unit tests for audio checkpoint functionality (BEAN-001).
"""

import os
import sys
import tempfile
import shutil
import wave
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# pyaudio mock is installed by conftest.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

mock_pyaudio = sys.modules['pyaudio']

from audio.recorder import AudioRecorder  # noqa: E402


def _make_fake_frames(count, chunk_size=1024):
    """Generate fake audio frames (16-bit mono silence)."""
    return [b'\x00\x00' * chunk_size for _ in range(count)]


class TestCheckpointCreation(unittest.TestCase):
    """Test that checkpoint files are created when recording starts."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orig_dir = os.getcwd()
        os.chdir(self.temp_dir)

        # Create a recorder with short checkpoint interval
        self.mock_pa = MagicMock()
        self.mock_pa.get_sample_size.return_value = 2  # 16-bit
        mock_pyaudio.PyAudio.return_value = self.mock_pa

        mock_stream = MagicMock()
        self.mock_pa.open.return_value = mock_stream

        self.recorder = AudioRecorder(
            sample_rate=44100,
            chunk_size=1024,
            channels=1,
            checkpoint_interval=1,  # 1 second for fast testing
        )

        # Set output_path (normally done by start_recording)
        recordings_dir = Path("recordings")
        recordings_dir.mkdir(exist_ok=True)
        self.recorder.output_path = recordings_dir / "recording-test.wav"

    def tearDown(self):
        # Cancel any timers
        if self.recorder._checkpoint_timer:
            self.recorder._checkpoint_timer.cancel()
        self.recorder.is_recording = False
        os.chdir(self.orig_dir)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_checkpoint_path_set_on_start(self):
        """Checkpoint path is set when recording starts via PyAudio."""
        self.recorder._try_pyaudio_recording()
        self.assertIsNotNone(self.recorder._checkpoint_path)
        self.assertIn('.checkpoint.wav', str(self.recorder._checkpoint_path))

    def test_checkpoint_not_created_when_disabled(self):
        """No checkpoint when interval is 0."""
        self.recorder.checkpoint_interval = 0
        self.recorder._try_pyaudio_recording()
        self.assertIsNone(self.recorder._checkpoint_path)

    def test_checkpoint_timer_started(self):
        """Timer is started when checkpointing begins."""
        self.recorder._try_pyaudio_recording()
        self.assertIsNotNone(self.recorder._checkpoint_timer)
        self.assertTrue(self.recorder._checkpoint_timer.is_alive())


class TestCheckpointFlush(unittest.TestCase):
    """Test that checkpoint files are flushed correctly."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orig_dir = os.getcwd()
        os.chdir(self.temp_dir)

        self.mock_pa = MagicMock()
        self.mock_pa.get_sample_size.return_value = 2
        mock_pyaudio.PyAudio.return_value = self.mock_pa

        self.recorder = AudioRecorder(
            sample_rate=44100,
            chunk_size=1024,
            channels=1,
            checkpoint_interval=30,
        )
        self.recorder.is_recording = True

        # Set up checkpoint path manually
        recordings_dir = Path("recordings")
        recordings_dir.mkdir(exist_ok=True)
        self.recorder._checkpoint_path = (
            recordings_dir / "recording-test.checkpoint.wav"
        )
        self.recorder.output_path = recordings_dir / "recording-test.wav"

    def tearDown(self):
        if self.recorder._checkpoint_timer:
            self.recorder._checkpoint_timer.cancel()
        self.recorder.is_recording = False
        os.chdir(self.orig_dir)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_flush_creates_valid_wav(self):
        """Flushed checkpoint is a valid WAV file."""
        self.recorder.frames = _make_fake_frames(100)
        self.recorder._flush_checkpoint()

        cp = self.recorder._checkpoint_path
        self.assertTrue(cp.exists())

        with wave.open(str(cp), 'rb') as wf:
            self.assertEqual(wf.getnchannels(), 1)
            self.assertEqual(wf.getsampwidth(), 2)
            self.assertEqual(wf.getframerate(), 44100)
            self.assertEqual(wf.getnframes(), 100 * 1024)

    def test_flush_with_no_frames_skips(self):
        """Flush with empty frames does not create a file."""
        self.recorder.frames = []
        self.recorder._flush_checkpoint()

        cp = self.recorder._checkpoint_path
        self.assertFalse(cp.exists())

    def test_flush_updates_last_flushed_count(self):
        """Last flushed count is updated after flush."""
        self.recorder.frames = _make_fake_frames(50)
        self.recorder._flush_checkpoint()
        self.assertEqual(self.recorder._last_flushed_count, 50)

    def test_multiple_flushes_grow_file(self):
        """Each flush rewrites the checkpoint with all frames."""
        self.recorder.frames = _make_fake_frames(50)
        self.recorder._flush_checkpoint()

        with wave.open(str(self.recorder._checkpoint_path), 'rb') as wf:
            frames_after_first = wf.getnframes()

        # Add more frames
        self.recorder.frames.extend(_make_fake_frames(50))
        self.recorder._flush_checkpoint()

        with wave.open(str(self.recorder._checkpoint_path), 'rb') as wf:
            frames_after_second = wf.getnframes()

        self.assertEqual(frames_after_first, 50 * 1024)
        self.assertEqual(frames_after_second, 100 * 1024)


class TestCheckpointFinalization(unittest.TestCase):
    """Test that stop_recording finalizes the checkpoint."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orig_dir = os.getcwd()
        os.chdir(self.temp_dir)

        self.mock_pa = MagicMock()
        self.mock_pa.get_sample_size.return_value = 2
        mock_pyaudio.PyAudio.return_value = self.mock_pa

        self.recorder = AudioRecorder(
            sample_rate=44100,
            chunk_size=1024,
            channels=1,
            checkpoint_interval=30,
        )

        recordings_dir = Path("recordings")
        recordings_dir.mkdir(exist_ok=True)
        self.recorder._checkpoint_path = (
            recordings_dir / "recording-test.checkpoint.wav"
        )
        self.recorder.output_path = recordings_dir / "recording-test.wav"

    def tearDown(self):
        if self.recorder._checkpoint_timer:
            self.recorder._checkpoint_timer.cancel()
        self.recorder.is_recording = False
        os.chdir(self.orig_dir)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_finalize_renames_checkpoint(self):
        """Finalize renames checkpoint.wav to output path."""
        self.recorder.frames = _make_fake_frames(100)

        result = self.recorder._finalize_checkpoint()

        self.assertEqual(result, self.recorder.output_path)
        self.assertTrue(self.recorder.output_path.exists())
        self.assertFalse(
            Path("recordings/recording-test.checkpoint.wav").exists()
        )

    def test_finalize_produces_valid_wav(self):
        """Finalized file is a valid WAV with all frames."""
        self.recorder.frames = _make_fake_frames(200)

        self.recorder._finalize_checkpoint()

        with wave.open(str(self.recorder.output_path), 'rb') as wf:
            self.assertEqual(wf.getnchannels(), 1)
            self.assertEqual(wf.getsampwidth(), 2)
            self.assertEqual(wf.getframerate(), 44100)
            self.assertEqual(wf.getnframes(), 200 * 1024)

    def test_no_checkpoint_files_after_clean_stop(self):
        """No .checkpoint.wav files remain after finalization."""
        self.recorder.frames = _make_fake_frames(50)
        self.recorder._finalize_checkpoint()

        checkpoint_files = list(
            Path("recordings").glob("*.checkpoint.wav")
        )
        self.assertEqual(len(checkpoint_files), 0)

    def test_finalize_cancels_timer(self):
        """Finalize cancels the checkpoint timer."""
        timer = MagicMock()
        self.recorder._checkpoint_timer = timer
        self.recorder.frames = _make_fake_frames(10)

        self.recorder._finalize_checkpoint()

        timer.cancel.assert_called_once()

    def test_finalize_with_no_checkpoint_returns_none(self):
        """Finalize with no checkpoint path returns None."""
        self.recorder._checkpoint_path = None
        result = self.recorder._finalize_checkpoint()
        self.assertIsNone(result)


class TestCheckpointRecovery(unittest.TestCase):
    """Test orphaned checkpoint recovery."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orig_dir = os.getcwd()
        os.chdir(self.temp_dir)
        self.recordings_dir = Path("recordings")
        self.recordings_dir.mkdir(exist_ok=True)

    def tearDown(self):
        os.chdir(self.orig_dir)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_checkpoint_wav(self, name, nframes=100):
        """Helper to create a valid checkpoint WAV file."""
        path = self.recordings_dir / name
        with wave.open(str(path), 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(44100)
            wf.writeframes(b'\x00\x00' * nframes)
        return path

    def test_recover_finds_orphaned_checkpoints(self):
        """Recovery finds and renames orphaned checkpoint files."""
        self._create_checkpoint_wav(
            "recording-20260210-150000.checkpoint.wav"
        )

        recovered = AudioRecorder.recover_checkpoints("recordings")

        self.assertEqual(len(recovered), 1)
        self.assertIn("-recovered.wav", str(recovered[0]))
        self.assertTrue(recovered[0].exists())

    def test_recover_removes_checkpoint_marker(self):
        """Recovered files no longer have .checkpoint in name."""
        self._create_checkpoint_wav(
            "recording-20260210-150000.checkpoint.wav"
        )

        recovered = AudioRecorder.recover_checkpoints("recordings")

        for path in recovered:
            self.assertNotIn(".checkpoint", str(path))

    def test_recover_multiple_checkpoints(self):
        """Recovery handles multiple orphaned checkpoints."""
        self._create_checkpoint_wav(
            "recording-20260210-150000.checkpoint.wav"
        )
        self._create_checkpoint_wav(
            "recording-20260210-160000.checkpoint.wav"
        )

        recovered = AudioRecorder.recover_checkpoints("recordings")

        self.assertEqual(len(recovered), 2)

    def test_recover_skips_corrupt_files(self):
        """Recovery skips corrupt/unreadable checkpoint files."""
        # Create a corrupt file
        corrupt_path = self.recordings_dir / "bad.checkpoint.wav"
        corrupt_path.write_bytes(b"not a wav file")

        # Create a valid one
        self._create_checkpoint_wav(
            "recording-20260210-150000.checkpoint.wav"
        )

        recovered = AudioRecorder.recover_checkpoints("recordings")

        self.assertEqual(len(recovered), 1)
        # Corrupt file should still exist (not deleted)
        self.assertTrue(corrupt_path.exists())

    def test_recover_skips_empty_checkpoints(self):
        """Recovery skips checkpoint files with zero frames."""
        self._create_checkpoint_wav(
            "recording-20260210-150000.checkpoint.wav", nframes=0
        )

        recovered = AudioRecorder.recover_checkpoints("recordings")

        self.assertEqual(len(recovered), 0)

    def test_recover_empty_directory(self):
        """Recovery returns empty list when no checkpoints exist."""
        recovered = AudioRecorder.recover_checkpoints("recordings")
        self.assertEqual(recovered, [])

    def test_recover_nonexistent_directory(self):
        """Recovery returns empty list for nonexistent directory."""
        recovered = AudioRecorder.recover_checkpoints("/nonexistent")
        self.assertEqual(recovered, [])


class TestAudioContinuity(unittest.TestCase):
    """Test that checkpoint boundaries don't cause audio gaps."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orig_dir = os.getcwd()
        os.chdir(self.temp_dir)

        self.mock_pa = MagicMock()
        self.mock_pa.get_sample_size.return_value = 2
        mock_pyaudio.PyAudio.return_value = self.mock_pa

        self.recorder = AudioRecorder(
            sample_rate=44100,
            chunk_size=1024,
            channels=1,
            checkpoint_interval=30,
        )

        recordings_dir = Path("recordings")
        recordings_dir.mkdir(exist_ok=True)
        self.recorder._checkpoint_path = (
            recordings_dir / "recording-test.checkpoint.wav"
        )
        self.recorder.output_path = recordings_dir / "recording-test.wav"
        self.recorder.is_recording = True

    def tearDown(self):
        if self.recorder._checkpoint_timer:
            self.recorder._checkpoint_timer.cancel()
        self.recorder.is_recording = False
        os.chdir(self.orig_dir)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_frames_contiguous_across_flushes(self):
        """Frames written across multiple flushes are contiguous."""
        # Create distinguishable frame data
        frame_a = b'\x01\x00' * 1024  # Low value
        frame_b = b'\x02\x00' * 1024  # Higher value
        frame_c = b'\x03\x00' * 1024  # Highest value

        self.recorder.frames = [frame_a, frame_b]
        self.recorder._flush_checkpoint()

        self.recorder.frames.append(frame_c)
        self.recorder._finalize_checkpoint()

        with wave.open(str(self.recorder.output_path), 'rb') as wf:
            raw = wf.readframes(wf.getnframes())

        # Verify all 3 frames are present in order
        expected = frame_a + frame_b + frame_c
        self.assertEqual(raw, expected)

    def test_finalized_matches_direct_save(self):
        """Checkpoint-finalized output matches what direct save produces."""
        frames = _make_fake_frames(150)
        self.recorder.frames = list(frames)

        # Save via checkpoint finalization
        self.recorder._finalize_checkpoint()

        with wave.open(str(self.recorder.output_path), 'rb') as wf:
            checkpoint_data = wf.readframes(wf.getnframes())

        # Save via direct method
        direct_path = Path("recordings") / "direct.wav"
        with wave.open(str(direct_path), 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(44100)
            wf.writeframes(b''.join(frames))

        with wave.open(str(direct_path), 'rb') as wf:
            direct_data = wf.readframes(wf.getnframes())

        self.assertEqual(checkpoint_data, direct_data)


if __name__ == '__main__':
    unittest.main()
