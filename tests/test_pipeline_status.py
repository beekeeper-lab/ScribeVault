"""
Tests for pipeline status tracking (BEAN-009).
"""

import json
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gui.pipeline_status import (
    PipelineStatus, ALL_STAGES,
    STAGE_RECORDING, STAGE_TRANSCRIPTION, STAGE_SUMMARIZATION, STAGE_VAULT_SAVE,
    STATUS_PENDING, STATUS_RUNNING, STATUS_SUCCESS, STATUS_FAILED, STATUS_SKIPPED,
)


class TestPipelineStatus(unittest.TestCase):
    """Test cases for PipelineStatus data model."""

    def test_initial_state(self):
        """All stages start as pending."""
        ps = PipelineStatus()
        for stage in ALL_STAGES:
            info = ps.get_stage(stage)
            self.assertEqual(info['status'], STATUS_PENDING)
            self.assertIsNone(info['error'])
            self.assertIsNone(info['duration'])

    def test_start_stage(self):
        """Starting a stage sets it to running."""
        ps = PipelineStatus()
        ps.start_stage(STAGE_TRANSCRIPTION)
        info = ps.get_stage(STAGE_TRANSCRIPTION)
        self.assertEqual(info['status'], STATUS_RUNNING)

    def test_complete_stage(self):
        """Completing a stage sets it to success with duration."""
        ps = PipelineStatus()
        ps.start_stage(STAGE_RECORDING)
        ps.complete_stage(STAGE_RECORDING)
        info = ps.get_stage(STAGE_RECORDING)
        self.assertEqual(info['status'], STATUS_SUCCESS)
        self.assertIsNone(info['error'])
        self.assertIsNotNone(info['duration'])
        self.assertGreaterEqual(info['duration'], 0)

    def test_fail_stage(self):
        """Failing a stage records error message and duration."""
        ps = PipelineStatus()
        ps.start_stage(STAGE_SUMMARIZATION)
        ps.fail_stage(STAGE_SUMMARIZATION, "API rate limit exceeded")
        info = ps.get_stage(STAGE_SUMMARIZATION)
        self.assertEqual(info['status'], STATUS_FAILED)
        self.assertEqual(info['error'], "API rate limit exceeded")
        self.assertIsNotNone(info['duration'])

    def test_skip_stage(self):
        """Skipping a stage sets status to skipped."""
        ps = PipelineStatus()
        ps.skip_stage(STAGE_SUMMARIZATION)
        info = ps.get_stage(STAGE_SUMMARIZATION)
        self.assertEqual(info['status'], STATUS_SKIPPED)
        self.assertIsNone(info['error'])

    def test_has_failures(self):
        """has_failures detects failed stages."""
        ps = PipelineStatus()
        self.assertFalse(ps.has_failures())

        ps.complete_stage(STAGE_RECORDING)
        self.assertFalse(ps.has_failures())

        ps.fail_stage(STAGE_TRANSCRIPTION, "Service unavailable")
        self.assertTrue(ps.has_failures())

    def test_failed_stages(self):
        """failed_stages returns list of failed stage names."""
        ps = PipelineStatus()
        ps.complete_stage(STAGE_RECORDING)
        ps.fail_stage(STAGE_TRANSCRIPTION, "error1")
        ps.skip_stage(STAGE_SUMMARIZATION)
        ps.fail_stage(STAGE_VAULT_SAVE, "error2")

        failed = ps.failed_stages()
        self.assertEqual(sorted(failed), [STAGE_TRANSCRIPTION, STAGE_VAULT_SAVE])

    def test_unknown_stage_raises(self):
        """Operations on unknown stage names raise ValueError."""
        ps = PipelineStatus()
        with self.assertRaises(ValueError):
            ps.start_stage("unknown_stage")
        with self.assertRaises(ValueError):
            ps.complete_stage("unknown_stage")
        with self.assertRaises(ValueError):
            ps.fail_stage("unknown_stage", "err")
        with self.assertRaises(ValueError):
            ps.skip_stage("unknown_stage")
        with self.assertRaises(ValueError):
            ps.get_stage("unknown_stage")

    def test_serialization_roundtrip(self):
        """to_dict and from_dict preserve all state."""
        ps = PipelineStatus()
        ps.start_stage(STAGE_RECORDING)
        ps.complete_stage(STAGE_RECORDING)
        ps.start_stage(STAGE_TRANSCRIPTION)
        ps.fail_stage(STAGE_TRANSCRIPTION, "Timeout")
        ps.skip_stage(STAGE_SUMMARIZATION)
        # vault_save stays pending

        data = ps.to_dict()

        # Verify dict structure
        self.assertIn(STAGE_RECORDING, data)
        self.assertEqual(data[STAGE_RECORDING]['status'], STATUS_SUCCESS)
        self.assertEqual(data[STAGE_TRANSCRIPTION]['status'], STATUS_FAILED)
        self.assertEqual(data[STAGE_TRANSCRIPTION]['error'], "Timeout")
        self.assertEqual(data[STAGE_SUMMARIZATION]['status'], STATUS_SKIPPED)
        self.assertEqual(data[STAGE_VAULT_SAVE]['status'], STATUS_PENDING)

        # Roundtrip
        ps2 = PipelineStatus.from_dict(data)
        data2 = ps2.to_dict()
        self.assertEqual(data, data2)

    def test_json_serialization(self):
        """Pipeline status is JSON-serializable."""
        ps = PipelineStatus()
        ps.complete_stage(STAGE_RECORDING)
        ps.fail_stage(STAGE_TRANSCRIPTION, "API error")

        data = ps.to_dict()
        json_str = json.dumps(data)
        restored = json.loads(json_str)
        ps2 = PipelineStatus.from_dict(restored)

        self.assertEqual(ps2.get_stage(STAGE_RECORDING)['status'], STATUS_SUCCESS)
        self.assertEqual(ps2.get_stage(STAGE_TRANSCRIPTION)['error'], "API error")

    def test_from_dict_with_missing_stages(self):
        """from_dict handles partial data gracefully."""
        partial = {
            STAGE_RECORDING: {"status": STATUS_SUCCESS, "error": None, "duration": 1.5}
        }
        ps = PipelineStatus.from_dict(partial)
        self.assertEqual(ps.get_stage(STAGE_RECORDING)['status'], STATUS_SUCCESS)
        # Missing stages default to pending
        self.assertEqual(ps.get_stage(STAGE_TRANSCRIPTION)['status'], STATUS_PENDING)


class TestVaultPipelineStatusPersistence(unittest.TestCase):
    """Test pipeline status persistence in vault."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        from vault.manager import VaultManager
        self.vault_manager = VaultManager(vault_dir=self.temp_dir)

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_add_recording_with_pipeline_status(self):
        """Pipeline status is stored when adding a recording."""
        ps = PipelineStatus()
        ps.complete_stage(STAGE_RECORDING)
        ps.complete_stage(STAGE_TRANSCRIPTION)
        ps.skip_stage(STAGE_SUMMARIZATION)
        ps.complete_stage(STAGE_VAULT_SAVE)

        self.vault_manager.add_recording(
            filename="test.wav",
            pipeline_status=ps.to_dict()
        )

        recordings = self.vault_manager.get_recordings()
        self.assertEqual(len(recordings), 1)
        stored_status = recordings[0]['pipeline_status']
        self.assertIsInstance(stored_status, dict)
        self.assertEqual(stored_status[STAGE_RECORDING]['status'], STATUS_SUCCESS)
        self.assertEqual(stored_status[STAGE_SUMMARIZATION]['status'], STATUS_SKIPPED)

    def test_add_recording_without_pipeline_status(self):
        """Recordings without pipeline status work fine."""
        self.vault_manager.add_recording(filename="test.wav")
        recordings = self.vault_manager.get_recordings()
        self.assertEqual(len(recordings), 1)
        self.assertIsNone(recordings[0]['pipeline_status'])

    def test_update_pipeline_status(self):
        """Pipeline status can be updated after creation."""
        rec_id = self.vault_manager.add_recording(filename="test.wav")

        ps = PipelineStatus()
        ps.complete_stage(STAGE_RECORDING)
        ps.fail_stage(STAGE_TRANSCRIPTION, "timeout")

        self.vault_manager.update_recording(rec_id, pipeline_status=ps.to_dict())

        recordings = self.vault_manager.get_recordings()
        stored = recordings[0]['pipeline_status']
        self.assertEqual(stored[STAGE_TRANSCRIPTION]['status'], STATUS_FAILED)
        self.assertEqual(stored[STAGE_TRANSCRIPTION]['error'], "timeout")

    def test_pipeline_status_with_failed_stages(self):
        """Failed stage errors are preserved through storage."""
        ps = PipelineStatus()
        ps.complete_stage(STAGE_RECORDING)
        ps.fail_stage(STAGE_TRANSCRIPTION, "Whisper API returned 429: Rate limit exceeded")
        ps.skip_stage(STAGE_SUMMARIZATION)
        ps.complete_stage(STAGE_VAULT_SAVE)

        self.vault_manager.add_recording(
            filename="test_fail.wav",
            pipeline_status=ps.to_dict()
        )

        recordings = self.vault_manager.get_recordings()
        stored = recordings[0]['pipeline_status']

        # Verify the error message is preserved exactly
        self.assertEqual(
            stored[STAGE_TRANSCRIPTION]['error'],
            "Whisper API returned 429: Rate limit exceeded"
        )

    def test_pipeline_status_roundtrip(self):
        """Full roundtrip: PipelineStatus -> vault -> PipelineStatus."""
        ps = PipelineStatus()
        ps.start_stage(STAGE_RECORDING)
        ps.complete_stage(STAGE_RECORDING)
        ps.start_stage(STAGE_TRANSCRIPTION)
        ps.complete_stage(STAGE_TRANSCRIPTION)
        ps.start_stage(STAGE_SUMMARIZATION)
        ps.fail_stage(STAGE_SUMMARIZATION, "Model overloaded")
        ps.start_stage(STAGE_VAULT_SAVE)
        ps.complete_stage(STAGE_VAULT_SAVE)

        original_dict = ps.to_dict()

        self.vault_manager.add_recording(
            filename="roundtrip.wav",
            pipeline_status=original_dict
        )

        recordings = self.vault_manager.get_recordings()
        stored_dict = recordings[0]['pipeline_status']

        # Reconstruct PipelineStatus from stored data
        ps2 = PipelineStatus.from_dict(stored_dict)
        self.assertEqual(ps2.to_dict(), original_dict)


try:
    from PySide6.QtWidgets import QApplication  # noqa: F401
    HAS_PYSIDE6 = True
except ImportError:
    HAS_PYSIDE6 = False


@unittest.skipUnless(HAS_PYSIDE6, "PySide6 not available")
class TestRecordingWorkerStageSignals(unittest.TestCase):
    """Test RecordingWorker stage signal emissions."""

    def test_worker_emits_stage_signals_all_success(self):
        """Worker emits correct stage signals when all services succeed."""
        # Create a minimal wav file
        temp_dir = Path(tempfile.mkdtemp())
        try:
            audio_path = temp_dir / "test.wav"
            self._create_test_wav(audio_path)

            mock_whisper = MagicMock()
            mock_whisper.transcribe_audio.return_value = "Hello world"

            mock_summarizer = MagicMock()
            mock_summarizer.generate_summary_with_markdown.return_value = {
                'summary': 'Test summary',
                'markdown_path': '/tmp/test.md'
            }

            mock_vault = MagicMock()
            mock_vault.add_recording.return_value = 1

            services = {
                'whisper': mock_whisper,
                'summarizer': mock_summarizer,
                'vault': mock_vault,
                'generate_summary': True
            }

            from gui.qt_main_window import RecordingWorker

            worker = RecordingWorker(audio_path, services)

            # Collect stage updates
            stage_updates = []
            worker.stage_update.connect(lambda s, st, e: stage_updates.append((s, st, e)))

            results = []
            worker.finished.connect(lambda r: results.append(r))

            worker.run()

            # Verify stage signals
            stages_seen = {}
            for stage, status, error in stage_updates:
                if stage not in stages_seen:
                    stages_seen[stage] = []
                stages_seen[stage].append(status)

            # Each stage should have running then success
            self.assertIn(STATUS_RUNNING, stages_seen.get(STAGE_RECORDING, []))
            self.assertIn(STATUS_SUCCESS, stages_seen.get(STAGE_RECORDING, []))
            self.assertIn(STATUS_RUNNING, stages_seen.get(STAGE_TRANSCRIPTION, []))
            self.assertIn(STATUS_SUCCESS, stages_seen.get(STAGE_TRANSCRIPTION, []))
            self.assertIn(STATUS_RUNNING, stages_seen.get(STAGE_SUMMARIZATION, []))
            self.assertIn(STATUS_SUCCESS, stages_seen.get(STAGE_SUMMARIZATION, []))
            self.assertIn(STATUS_RUNNING, stages_seen.get(STAGE_VAULT_SAVE, []))
            self.assertIn(STATUS_SUCCESS, stages_seen.get(STAGE_VAULT_SAVE, []))

            # Verify result includes pipeline_status
            self.assertEqual(len(results), 1)
            self.assertIn('pipeline_status', results[0])

        finally:
            shutil.rmtree(temp_dir)

    def test_worker_emits_stage_signals_transcription_fails(self):
        """Worker emits failed signal when transcription raises."""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            audio_path = temp_dir / "test.wav"
            self._create_test_wav(audio_path)

            mock_whisper = MagicMock()
            mock_whisper.transcribe_audio.side_effect = Exception("API error 500")

            mock_vault = MagicMock()
            mock_vault.add_recording.return_value = 1

            services = {
                'whisper': mock_whisper,
                'summarizer': None,
                'vault': mock_vault,
                'generate_summary': False
            }

            from gui.qt_main_window import RecordingWorker

            worker = RecordingWorker(audio_path, services)

            stage_updates = []
            worker.stage_update.connect(lambda s, st, e: stage_updates.append((s, st, e)))

            results = []
            worker.finished.connect(lambda r: results.append(r))

            worker.run()

            # Find the transcription failure
            transcription_updates = [(st, e) for s, st, e in stage_updates if s == STAGE_TRANSCRIPTION]
            statuses = [st for st, e in transcription_updates]
            self.assertIn(STATUS_RUNNING, statuses)
            self.assertIn(STATUS_FAILED, statuses)

            # Find the error message
            failed = [(st, e) for st, e in transcription_updates if st == STATUS_FAILED]
            self.assertEqual(failed[0][1], "API error 500")

            # Pipeline should still complete (vault save should succeed)
            vault_updates = [(st, e) for s, st, e in stage_updates if s == STAGE_VAULT_SAVE]
            vault_statuses = [st for st, e in vault_updates]
            self.assertIn(STATUS_SUCCESS, vault_statuses)

            # Result should show failures
            self.assertEqual(len(results), 1)
            ps = results[0]['pipeline_status']
            self.assertEqual(ps[STAGE_TRANSCRIPTION]['status'], STATUS_FAILED)

        finally:
            shutil.rmtree(temp_dir)

    def test_worker_skips_stages_when_services_unavailable(self):
        """Worker emits skipped signals when services are None."""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            audio_path = temp_dir / "test.wav"
            self._create_test_wav(audio_path)

            services = {
                'whisper': None,
                'summarizer': None,
                'vault': None,
                'generate_summary': True
            }

            from gui.qt_main_window import RecordingWorker

            worker = RecordingWorker(audio_path, services)

            stage_updates = []
            worker.stage_update.connect(lambda s, st, e: stage_updates.append((s, st, e)))

            results = []
            worker.finished.connect(lambda r: results.append(r))

            worker.run()

            # Transcription, summarization, and vault should be skipped
            for stage in [STAGE_TRANSCRIPTION, STAGE_SUMMARIZATION, STAGE_VAULT_SAVE]:
                updates = [st for s, st, e in stage_updates if s == stage]
                self.assertIn(STATUS_SKIPPED, updates, f"{stage} should be skipped")

            # Recording should still succeed
            recording_updates = [st for s, st, e in stage_updates if s == STAGE_RECORDING]
            self.assertIn(STATUS_SUCCESS, recording_updates)

        finally:
            shutil.rmtree(temp_dir)

    @staticmethod
    def _create_test_wav(path: Path):
        """Create a minimal valid WAV file for testing."""
        import wave
        with wave.open(str(path), 'wb') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(44100)
            f.writeframes(b'\x00\x00' * 44100)  # 1 second of silence


if __name__ == '__main__':
    unittest.main()
