"""
Unit tests for AudioSettings dataclass and audio quality presets.
"""

import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config.settings import (  # noqa: E402
    AudioSettings,
    AppSettings,
    AUDIO_PRESETS,
    SettingsManager,
    TranscriptionSettings,
    SummarizationSettings,
    UISettings,
)


class TestAudioPresets(unittest.TestCase):
    """Test AUDIO_PRESETS dictionary."""

    def test_presets_exist(self):
        self.assertIn("voice", AUDIO_PRESETS)
        self.assertIn("standard", AUDIO_PRESETS)
        self.assertIn("high_quality", AUDIO_PRESETS)

    def test_voice_preset_values(self):
        p = AUDIO_PRESETS["voice"]
        self.assertEqual(p["sample_rate"], 16000)
        self.assertEqual(p["channels"], 1)

    def test_standard_preset_values(self):
        p = AUDIO_PRESETS["standard"]
        self.assertEqual(p["sample_rate"], 44100)
        self.assertEqual(p["channels"], 1)

    def test_high_quality_preset_values(self):
        p = AUDIO_PRESETS["high_quality"]
        self.assertEqual(p["sample_rate"], 44100)
        self.assertEqual(p["channels"], 2)

    def test_all_presets_have_required_keys(self):
        required = {"label", "sample_rate", "channels", "description"}
        for name, preset in AUDIO_PRESETS.items():
            self.assertTrue(
                required.issubset(preset.keys()),
                f"Preset {name} missing keys: {required - preset.keys()}"
            )


class TestAudioSettings(unittest.TestCase):
    """Test AudioSettings dataclass."""

    def test_defaults(self):
        s = AudioSettings()
        self.assertEqual(s.preset, "standard")
        self.assertEqual(s.sample_rate, 44100)
        self.assertEqual(s.channels, 1)
        self.assertEqual(s.chunk_size, 1024)
        self.assertIsNone(s.input_device_index)
        self.assertEqual(s.input_device_name, "System Default")

    def test_voice_preset_creation(self):
        s = AudioSettings(preset="voice", sample_rate=16000, channels=1)
        self.assertEqual(s.preset, "voice")
        self.assertEqual(s.sample_rate, 16000)
        self.assertEqual(s.channels, 1)

    def test_high_quality_preset_creation(self):
        s = AudioSettings(
            preset="high_quality", sample_rate=44100, channels=2
        )
        self.assertEqual(s.preset, "high_quality")
        self.assertEqual(s.channels, 2)

    def test_invalid_preset_raises(self):
        with self.assertRaises(ValueError):
            AudioSettings(preset="invalid_preset")

    def test_invalid_sample_rate_raises(self):
        with self.assertRaises(ValueError):
            AudioSettings(sample_rate=12345)

    def test_invalid_channels_raises(self):
        with self.assertRaises(ValueError):
            AudioSettings(channels=5)

    def test_invalid_chunk_size_low(self):
        with self.assertRaises(ValueError):
            AudioSettings(chunk_size=64)

    def test_invalid_chunk_size_high(self):
        with self.assertRaises(ValueError):
            AudioSettings(chunk_size=99999)

    def test_apply_preset_voice(self):
        s = AudioSettings(preset="voice")
        s.apply_preset()
        self.assertEqual(s.sample_rate, 16000)
        self.assertEqual(s.channels, 1)

    def test_apply_preset_high_quality(self):
        s = AudioSettings(preset="high_quality")
        s.apply_preset()
        self.assertEqual(s.sample_rate, 44100)
        self.assertEqual(s.channels, 2)

    def test_device_index_accepted(self):
        s = AudioSettings(input_device_index=3, input_device_name="USB Mic")
        self.assertEqual(s.input_device_index, 3)
        self.assertEqual(s.input_device_name, "USB Mic")


class TestFileSizeEstimation(unittest.TestCase):
    """Test file size estimation."""

    def test_voice_file_size(self):
        # 16000 Hz * 1 ch * 2 bytes = 32000 B/s = 1.92 MB/min
        size = AudioSettings.estimate_file_size_per_minute(16000, 1)
        self.assertAlmostEqual(size, 1.83, places=1)

    def test_standard_file_size(self):
        # 44100 Hz * 1 ch * 2 bytes = 88200 B/s = 5.05 MB/min
        size = AudioSettings.estimate_file_size_per_minute(44100, 1)
        self.assertAlmostEqual(size, 5.05, places=1)

    def test_high_quality_file_size(self):
        # 44100 Hz * 2 ch * 2 bytes = 176400 B/s = 10.09 MB/min
        size = AudioSettings.estimate_file_size_per_minute(44100, 2)
        self.assertAlmostEqual(size, 10.09, places=1)

    def test_instance_method(self):
        s = AudioSettings(preset="voice", sample_rate=16000, channels=1)
        size = s.get_file_size_per_minute()
        self.assertAlmostEqual(size, 1.83, places=1)


class TestAppSettingsWithAudio(unittest.TestCase):
    """Test AppSettings integration with AudioSettings."""

    def test_default_audio_settings(self):
        s = AppSettings(
            transcription=TranscriptionSettings(),
            summarization=SummarizationSettings(),
            ui=UISettings(),
        )
        self.assertIsInstance(s.audio, AudioSettings)
        self.assertEqual(s.audio.preset, "standard")

    def test_explicit_audio_settings(self):
        audio = AudioSettings(
            preset="voice", sample_rate=16000, channels=1
        )
        s = AppSettings(
            transcription=TranscriptionSettings(),
            summarization=SummarizationSettings(),
            ui=UISettings(),
            audio=audio,
        )
        self.assertEqual(s.audio.preset, "voice")


class TestSettingsManagerAudioPersistence(unittest.TestCase):
    """Test that audio settings persist through save/load."""

    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "settings.json")

            # Save settings with audio config
            mgr = SettingsManager(config_file=config_path)
            mgr.settings.audio = AudioSettings(
                preset="voice",
                sample_rate=16000,
                channels=1,
                input_device_name="Test Mic",
            )
            mgr.save_settings()

            # Reload
            mgr2 = SettingsManager(config_file=config_path)
            self.assertEqual(mgr2.settings.audio.preset, "voice")
            self.assertEqual(mgr2.settings.audio.sample_rate, 16000)
            self.assertEqual(mgr2.settings.audio.channels, 1)
            self.assertEqual(
                mgr2.settings.audio.input_device_name, "Test Mic"
            )

    def test_load_without_audio_section(self):
        """Loading config that has no 'audio' key should use defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "settings.json")
            data = {
                "transcription": {},
                "summarization": {},
                "ui": {},
                "recordings_dir": "recordings",
                "vault_dir": "vault",
            }
            with open(config_path, "w") as f:
                json.dump(data, f)

            mgr = SettingsManager(config_file=config_path)
            self.assertEqual(mgr.settings.audio.preset, "standard")
            self.assertEqual(mgr.settings.audio.sample_rate, 44100)


class TestAudioRecorderDeviceParam(unittest.TestCase):
    """Test that AudioRecorder accepts input_device_index."""

    def test_init_with_device_index(self):
        mock_pa = MagicMock()
        with patch.dict('sys.modules', {'pyaudio': MagicMock()}):
            import importlib
            import audio.recorder as rec_mod
            importlib.reload(rec_mod)
            rec_mod.pyaudio.PyAudio = MagicMock(return_value=mock_pa)

            rec = rec_mod.AudioRecorder(
                sample_rate=16000,
                channels=1,
                input_device_index=2,
            )
            self.assertEqual(rec.sample_rate, 16000)
            self.assertEqual(rec.channels, 1)
            self.assertEqual(rec.input_device_index, 2)

    def test_init_without_device_index(self):
        mock_pa = MagicMock()
        with patch.dict('sys.modules', {'pyaudio': MagicMock()}):
            import importlib
            import audio.recorder as rec_mod
            importlib.reload(rec_mod)
            rec_mod.pyaudio.PyAudio = MagicMock(return_value=mock_pa)

            rec = rec_mod.AudioRecorder()
            self.assertIsNone(rec.input_device_index)


if __name__ == '__main__':
    unittest.main()
