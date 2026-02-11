"""
Unit tests for DiarizationSettings dataclass and settings persistence.
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config.settings import (  # noqa: E402
    AppSettings,
    DiarizationSettings,
    SettingsManager,
    SummarizationSettings,
    TranscriptionSettings,
    UISettings,
)


class TestDiarizationSettingsDefaults(unittest.TestCase):
    """Test DiarizationSettings default values and validation."""

    def test_defaults(self):
        s = DiarizationSettings()
        self.assertTrue(s.enabled)
        self.assertEqual(s.num_speakers, 0)
        self.assertAlmostEqual(s.sensitivity, 0.5)

    def test_custom_values(self):
        s = DiarizationSettings(enabled=False, num_speakers=4, sensitivity=0.8)
        self.assertFalse(s.enabled)
        self.assertEqual(s.num_speakers, 4)
        self.assertAlmostEqual(s.sensitivity, 0.8)

    def test_num_speakers_zero_auto(self):
        s = DiarizationSettings(num_speakers=0)
        self.assertEqual(s.num_speakers, 0)

    def test_num_speakers_valid_range(self):
        for n in (0, 2, 3, 4, 5, 6):
            s = DiarizationSettings(num_speakers=n)
            self.assertEqual(s.num_speakers, n)

    def test_num_speakers_negative_raises(self):
        with self.assertRaises(ValueError):
            DiarizationSettings(num_speakers=-1)

    def test_num_speakers_too_high_raises(self):
        with self.assertRaises(ValueError):
            DiarizationSettings(num_speakers=7)

    def test_sensitivity_min_boundary(self):
        s = DiarizationSettings(sensitivity=0.0)
        self.assertAlmostEqual(s.sensitivity, 0.0)

    def test_sensitivity_max_boundary(self):
        s = DiarizationSettings(sensitivity=1.0)
        self.assertAlmostEqual(s.sensitivity, 1.0)

    def test_sensitivity_below_min_raises(self):
        with self.assertRaises(ValueError):
            DiarizationSettings(sensitivity=-0.1)

    def test_sensitivity_above_max_raises(self):
        with self.assertRaises(ValueError):
            DiarizationSettings(sensitivity=1.1)


class TestDiarizationSettingsPersistence(unittest.TestCase):
    """Test DiarizationSettings round-trip through SettingsManager."""

    def test_round_trip_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "settings.json")

            mgr = SettingsManager(config_file=config_path)
            mgr.save_settings()

            mgr2 = SettingsManager(config_file=config_path)
            self.assertTrue(mgr2.settings.diarization.enabled)
            self.assertEqual(mgr2.settings.diarization.num_speakers, 0)
            self.assertAlmostEqual(mgr2.settings.diarization.sensitivity, 0.5)

    def test_round_trip_custom(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "settings.json")

            mgr = SettingsManager(config_file=config_path)
            mgr.settings.diarization = DiarizationSettings(
                enabled=False, num_speakers=3, sensitivity=0.75,
            )
            mgr.save_settings()

            mgr2 = SettingsManager(config_file=config_path)
            self.assertFalse(mgr2.settings.diarization.enabled)
            self.assertEqual(mgr2.settings.diarization.num_speakers, 3)
            self.assertAlmostEqual(mgr2.settings.diarization.sensitivity, 0.75)

    def test_load_without_diarization_section(self):
        """Loading config that has no 'diarization' key should use defaults."""
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
            self.assertTrue(mgr.settings.diarization.enabled)
            self.assertEqual(mgr.settings.diarization.num_speakers, 0)
            self.assertAlmostEqual(mgr.settings.diarization.sensitivity, 0.5)

    def test_json_contains_diarization(self):
        """Saved JSON file should contain diarization section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "settings.json")

            mgr = SettingsManager(config_file=config_path)
            mgr.settings.diarization = DiarizationSettings(
                enabled=False, num_speakers=5, sensitivity=0.2,
            )
            mgr.save_settings()

            with open(config_path) as f:
                data = json.load(f)

            self.assertIn("diarization", data)
            self.assertFalse(data["diarization"]["enabled"])
            self.assertEqual(data["diarization"]["num_speakers"], 5)
            self.assertAlmostEqual(data["diarization"]["sensitivity"], 0.2)


class TestAppSettingsWithDiarization(unittest.TestCase):
    """Test AppSettings integration with DiarizationSettings."""

    def test_diarization_field_exists(self):
        s = AppSettings(
            transcription=TranscriptionSettings(),
            summarization=SummarizationSettings(),
            diarization=DiarizationSettings(),
            ui=UISettings(),
        )
        self.assertIsInstance(s.diarization, DiarizationSettings)

    def test_explicit_diarization_values(self):
        d = DiarizationSettings(enabled=False, num_speakers=6, sensitivity=0.9)
        s = AppSettings(
            transcription=TranscriptionSettings(),
            summarization=SummarizationSettings(),
            diarization=d,
            ui=UISettings(),
        )
        self.assertFalse(s.diarization.enabled)
        self.assertEqual(s.diarization.num_speakers, 6)
        self.assertAlmostEqual(s.diarization.sensitivity, 0.9)


if __name__ == '__main__':
    unittest.main()
