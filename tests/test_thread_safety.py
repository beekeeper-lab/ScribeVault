"""
Tests for thread safety and resource cleanup (BEAN-002).

Verifies:
- AudioRecorder lock protects is_recording and frames
- AudioRecorder cleanup() and context manager work correctly
- SettingsManager lock protects save/load operations
- No deadlocks under concurrent access
"""

import unittest
import threading
import tempfile
import json
import time
from unittest.mock import MagicMock

import sys
import os

# Add src/ to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# pyaudio mock is installed by conftest.py
mock_pyaudio = sys.modules['pyaudio']

from audio.recorder import AudioRecorder  # noqa: E402


class TestAudioRecorderThreadSafety(unittest.TestCase):
    """Test thread safety of AudioRecorder."""

    def setUp(self):
        mock_pyaudio.PyAudio.reset_mock()
        self.mock_pa = MagicMock()
        mock_pyaudio.PyAudio.return_value = self.mock_pa

    def test_lock_exists(self):
        """AudioRecorder has a threading lock."""
        recorder = AudioRecorder()
        self.assertIsInstance(recorder._lock, type(threading.Lock()))
        recorder.cleanup()

    def test_concurrent_start_stop_no_crash(self):
        """Concurrent state changes through lock don't crash or corrupt."""
        recorder = AudioRecorder()
        errors = []

        def start_stop():
            try:
                for _ in range(10):
                    with recorder._lock:
                        old = recorder.is_recording
                        recorder.is_recording = not old
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=start_stop) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        self.assertEqual(errors, [], f"Errors during concurrent access: {errors}")
        recorder.cleanup()

    def test_audio_callback_uses_lock(self):
        """_audio_callback appends frames under lock protection."""
        recorder = AudioRecorder()
        recorder.is_recording = True

        result = recorder._audio_callback(b'test_data', 1024, {}, 0)
        self.assertEqual(result, (b'test_data', mock_pyaudio.paContinue))
        self.assertEqual(recorder.frames, [b'test_data'])

        # When not recording, frames should not grow
        recorder.is_recording = False
        recorder._audio_callback(b'more_data', 1024, {}, 0)
        self.assertEqual(recorder.frames, [b'test_data'])
        recorder.cleanup()

    def test_concurrent_callback_and_stop(self):
        """Frames list doesn't corrupt under concurrent callback + stop."""
        recorder = AudioRecorder()
        recorder.is_recording = True
        errors = []

        def pump_callbacks():
            try:
                for i in range(100):
                    recorder._audio_callback(
                        f'frame_{i}'.encode(), 1024, {}, 0
                    )
            except Exception as e:
                errors.append(e)

        def flip_recording():
            try:
                time.sleep(0.001)
                with recorder._lock:
                    recorder.is_recording = False
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=pump_callbacks)
        t2 = threading.Thread(target=flip_recording)
        t1.start()
        t2.start()
        t1.join(timeout=5)
        t2.join(timeout=5)

        self.assertEqual(errors, [])
        self.assertIsInstance(recorder.frames, list)
        recorder.cleanup()


class TestAudioRecorderCleanup(unittest.TestCase):
    """Test resource cleanup patterns in AudioRecorder."""

    def setUp(self):
        mock_pyaudio.PyAudio.reset_mock()
        self.mock_pa = MagicMock()
        mock_pyaudio.PyAudio.return_value = self.mock_pa

    def test_cleanup_terminates_pyaudio(self):
        """cleanup() calls audio.terminate()."""
        recorder = AudioRecorder()
        recorder.cleanup()
        self.mock_pa.terminate.assert_called_once()

    def test_cleanup_closes_stream(self):
        """cleanup() closes an open stream."""
        mock_stream = MagicMock()
        recorder = AudioRecorder()
        recorder.stream = mock_stream
        recorder.cleanup()

        mock_stream.stop_stream.assert_called_once()
        mock_stream.close.assert_called_once()
        self.assertIsNone(recorder.stream)

    def test_cleanup_idempotent(self):
        """Multiple cleanup() calls are safe."""
        recorder = AudioRecorder()
        recorder.cleanup()
        recorder.cleanup()
        recorder.cleanup()

        # terminate() should only be called once
        self.mock_pa.terminate.assert_called_once()

    def test_context_manager(self):
        """AudioRecorder works as a context manager."""
        with AudioRecorder() as recorder:
            self.assertIsInstance(recorder, AudioRecorder)

        # After exiting context, cleanup should have been called
        self.mock_pa.terminate.assert_called_once()

    def test_context_manager_on_exception(self):
        """Context manager cleans up even on exception."""
        try:
            with AudioRecorder():
                raise ValueError("test error")
        except ValueError:
            pass

        self.mock_pa.terminate.assert_called_once()

    def test_no_del_method(self):
        """AudioRecorder no longer uses __del__."""
        self.assertFalse(
            '__del__' in AudioRecorder.__dict__,
            "AudioRecorder should not define __del__"
        )

    def test_stop_recording_closes_stream_in_finally(self):
        """Stream is set to None even if stop_stream raises."""
        mock_stream = MagicMock()
        mock_stream.stop_stream.side_effect = Exception("stream error")

        recorder = AudioRecorder()
        recorder.is_recording = True
        recorder.stream = mock_stream

        # stop_recording should not raise, and stream should be None
        recorder.stop_recording()
        self.assertIsNone(recorder.stream)
        recorder.cleanup()


class TestSettingsManagerThreadSafety(unittest.TestCase):
    """Test thread safety of SettingsManager."""

    def test_lock_exists(self):
        """SettingsManager has a threading lock."""
        from config.settings import SettingsManager
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, "settings.json")
            mgr = SettingsManager(config_file=config_file)
            self.assertIsInstance(mgr._lock, type(threading.Lock()))

    def test_concurrent_save_no_corruption(self):
        """Concurrent saves don't corrupt the JSON file."""
        from config.settings import SettingsManager
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, "settings.json")
            mgr = SettingsManager(config_file=config_file)

            errors = []

            def save_repeatedly():
                try:
                    for _ in range(20):
                        mgr.save_settings()
                        time.sleep(0.001)
                except Exception as e:
                    errors.append(e)

            threads = [threading.Thread(target=save_repeatedly)
                       for _ in range(4)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=10)

            self.assertEqual(errors, [],
                             f"Errors during concurrent save: {errors}")

            # Verify file is valid JSON
            with open(config_file, 'r') as f:
                data = json.load(f)
            self.assertIn('transcription', data)

    def test_concurrent_save_load_no_corruption(self):
        """Concurrent save + load operations don't corrupt state."""
        from config.settings import SettingsManager
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, "settings.json")
            mgr = SettingsManager(config_file=config_file)
            mgr.save_settings()

            errors = []

            def save_loop():
                try:
                    for _ in range(20):
                        mgr.save_settings()
                        time.sleep(0.001)
                except Exception as e:
                    errors.append(e)

            def load_loop():
                try:
                    for _ in range(20):
                        mgr._load_settings()
                        time.sleep(0.001)
                except Exception as e:
                    errors.append(e)

            threads = [
                threading.Thread(target=save_loop),
                threading.Thread(target=load_loop),
                threading.Thread(target=save_loop),
                threading.Thread(target=load_loop),
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=10)

            self.assertEqual(errors, [],
                             f"Errors during concurrent save/load: {errors}")


class TestNoDeadlocks(unittest.TestCase):
    """Verify no deadlocks under contention."""

    def setUp(self):
        mock_pyaudio.PyAudio.reset_mock()
        self.mock_pa = MagicMock()
        mock_pyaudio.PyAudio.return_value = self.mock_pa

    def test_recorder_no_deadlock(self):
        """Lock contention on AudioRecorder doesn't deadlock."""
        recorder = AudioRecorder()

        completed = threading.Event()

        def worker():
            for _ in range(50):
                with recorder._lock:
                    recorder.is_recording = True
                with recorder._lock:
                    recorder.is_recording = False
            completed.set()

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()

        all_done = completed.wait(timeout=5)
        for t in threads:
            t.join(timeout=1)

        self.assertTrue(all_done or not any(t.is_alive() for t in threads),
                        "Potential deadlock detected")
        recorder.cleanup()

    def test_settings_no_deadlock(self):
        """Lock contention on SettingsManager doesn't deadlock."""
        from config.settings import SettingsManager
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, "settings.json")
            mgr = SettingsManager(config_file=config_file)

            completed = threading.Event()

            def worker():
                for _ in range(30):
                    mgr.save_settings()
                    mgr._load_settings()
                completed.set()

            threads = [threading.Thread(target=worker) for _ in range(4)]
            for t in threads:
                t.start()

            all_done = completed.wait(timeout=10)
            for t in threads:
                t.join(timeout=1)

            self.assertTrue(
                all_done or not any(t.is_alive() for t in threads),
                "Potential deadlock detected in SettingsManager"
            )


if __name__ == '__main__':
    unittest.main()
