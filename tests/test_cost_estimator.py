"""
Tests for CostEstimator with config-driven model pricing (BEAN-023).
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config.settings import CostEstimator, SummarizationSettings  # noqa: E402


class TestCostEstimatorConfigLoading(unittest.TestCase):
    """Tests for loading pricing from JSON config."""

    def setUp(self):
        # Reset cached pricing before each test
        CostEstimator._pricing = None
        CostEstimator._config_path = None

    def tearDown(self):
        CostEstimator._pricing = None
        CostEstimator._config_path = None

    def test_load_pricing_from_file(self):
        """Pricing loads correctly from a JSON file."""
        data = {
            "last_updated": "2026-01-15",
            "transcription": {
                "whisper-1": {"name": "Whisper", "cost_per_minute": 0.006}
            },
            "summarization": {
                "gpt-4o": {
                    "name": "GPT-4o",
                    "input_cost_per_1k_tokens": 0.0025,
                    "output_cost_per_1k_tokens": 0.01,
                }
            },
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            tmp_path = f.name

        try:
            pricing = CostEstimator.load_pricing(tmp_path)
            self.assertEqual(pricing["last_updated"], "2026-01-15")
            self.assertIn("gpt-4o", pricing["summarization"])
        finally:
            os.unlink(tmp_path)

    def test_fallback_on_missing_file(self):
        """Falls back to defaults when config file is missing."""
        pricing = CostEstimator.load_pricing("/nonexistent/path.json")
        self.assertIn("summarization", pricing)
        self.assertIn("gpt-4o-mini", pricing["summarization"])

    def test_get_last_updated(self):
        """get_last_updated returns the config value."""
        CostEstimator._pricing = {"last_updated": "2026-02-11"}
        self.assertEqual(CostEstimator.get_last_updated(), "2026-02-11")

    def test_get_summary_models(self):
        """get_summary_models returns model IDs from config."""
        CostEstimator._pricing = {
            "summarization": {
                "gpt-4o": {},
                "gpt-4o-mini": {},
                "gpt-4-turbo": {},
            }
        }
        models = CostEstimator.get_summary_models()
        self.assertEqual(models, ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"])


class TestCostEstimatorModelPricing(unittest.TestCase):
    """Tests for model-aware cost estimation."""

    def setUp(self):
        CostEstimator._pricing = {
            "last_updated": "2026-02-11",
            "transcription": {
                "whisper-1": {"name": "Whisper", "cost_per_minute": 0.006}
            },
            "summarization": {
                "gpt-4o": {
                    "name": "GPT-4o",
                    "input_cost_per_1k_tokens": 0.0025,
                    "output_cost_per_1k_tokens": 0.01,
                },
                "gpt-4o-mini": {
                    "name": "GPT-4o Mini",
                    "input_cost_per_1k_tokens": 0.00015,
                    "output_cost_per_1k_tokens": 0.0006,
                },
                "gpt-4-turbo": {
                    "name": "GPT-4 Turbo",
                    "input_cost_per_1k_tokens": 0.01,
                    "output_cost_per_1k_tokens": 0.03,
                },
            },
        }

    def tearDown(self):
        CostEstimator._pricing = None
        CostEstimator._config_path = None

    def test_get_model_pricing_known_model(self):
        """Returns correct pricing for a known model."""
        inp, out = CostEstimator.get_model_pricing("gpt-4o")
        self.assertAlmostEqual(inp, 0.0025)
        self.assertAlmostEqual(out, 0.01)

    def test_get_model_pricing_unknown_model_falls_back(self):
        """Unknown model falls back to gpt-4o-mini pricing."""
        inp, out = CostEstimator.get_model_pricing("unknown-model")
        self.assertAlmostEqual(inp, 0.00015)
        self.assertAlmostEqual(out, 0.0006)

    def test_estimate_summary_cost_varies_by_model(self):
        """Different models produce different cost estimates."""
        cost_mini = CostEstimator.estimate_summary_cost(60, "gpt-4o-mini")
        cost_turbo = CostEstimator.estimate_summary_cost(60, "gpt-4-turbo")
        self.assertGreater(cost_turbo["total"], cost_mini["total"])

    def test_estimate_summary_cost_structure(self):
        """Summary cost returns expected keys."""
        result = CostEstimator.estimate_summary_cost(60, "gpt-4o")
        expected_keys = {
            "input_tokens", "output_tokens", "input_cost",
            "output_cost", "total", "per_minute", "per_hour",
        }
        self.assertEqual(set(result.keys()), expected_keys)

    def test_estimate_openai_cost_with_model(self):
        """OpenAI cost estimation accepts model parameter."""
        cost = CostEstimator.estimate_openai_cost(60, True, "gpt-4-turbo")
        self.assertGreater(cost["transcription"], 0)
        self.assertGreater(cost["summary"], 0)
        self.assertAlmostEqual(
            cost["total"], cost["transcription"] + cost["summary"]
        )

    def test_estimate_openai_cost_no_summary(self):
        """OpenAI cost without summary has zero summary cost."""
        cost = CostEstimator.estimate_openai_cost(60, False)
        self.assertAlmostEqual(cost["summary"], 0.0)
        self.assertAlmostEqual(cost["total"], cost["transcription"])

    def test_estimate_local_cost_zero_transcription(self):
        """Local cost has zero transcription cost."""
        cost = CostEstimator.estimate_local_cost(60, True, "gpt-4o")
        self.assertAlmostEqual(cost["transcription"], 0.0)
        self.assertGreater(cost["summary"], 0)

    def test_get_whisper_cost_per_minute(self):
        """Whisper cost per minute comes from config."""
        self.assertAlmostEqual(
            CostEstimator.get_whisper_cost_per_minute(), 0.006
        )

    def test_get_cost_comparison(self):
        """Cost comparison returns openai, local, and savings."""
        result = CostEstimator.get_cost_comparison(60, True, "gpt-4o")
        self.assertIn("openai", result)
        self.assertIn("local", result)
        self.assertIn("savings", result)
        self.assertGreater(result["savings"]["amount"], 0)

    def test_zero_minutes_no_division_error(self):
        """Zero-minute estimate doesn't raise division errors."""
        cost = CostEstimator.estimate_summary_cost(0, "gpt-4o")
        self.assertAlmostEqual(cost["per_minute"], 0)
        self.assertAlmostEqual(cost["per_hour"], 0)


class TestSummarizationSettingsDefaults(unittest.TestCase):
    """Tests that SummarizationSettings defaults are updated."""

    def test_default_model_is_gpt4o_mini(self):
        """Default summarization model is gpt-4o-mini."""
        settings = SummarizationSettings()
        self.assertEqual(settings.model, "gpt-4o-mini")

    def test_default_service_is_openai(self):
        """Default service remains openai."""
        settings = SummarizationSettings()
        self.assertEqual(settings.service, "openai")


if __name__ == "__main__":
    unittest.main()
