"""
Unit tests for PromptTemplateManager and PromptTemplate.
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ai.prompt_templates import (  # noqa: E402
    PromptTemplate,
    PromptTemplateManager,
    BUILTIN_TEMPLATES,
)


class TestPromptTemplate(unittest.TestCase):
    """Tests for the PromptTemplate data class."""

    def test_create_template(self):
        """Test creating a prompt template."""
        t = PromptTemplate(
            template_id="test-1",
            name="Test Template",
            prompt_text="Summarize this text.",
        )
        self.assertEqual(t.template_id, "test-1")
        self.assertEqual(t.name, "Test Template")
        self.assertEqual(t.prompt_text, "Summarize this text.")
        self.assertFalse(t.is_builtin)
        self.assertIsNotNone(t.created_at)

    def test_to_dict(self):
        """Test serialization to dict."""
        t = PromptTemplate(
            template_id="test-1",
            name="Test",
            prompt_text="prompt",
            is_builtin=True,
            created_at="2026-01-01T00:00:00",
        )
        d = t.to_dict()
        self.assertEqual(d["template_id"], "test-1")
        self.assertEqual(d["name"], "Test")
        self.assertEqual(d["prompt_text"], "prompt")
        self.assertTrue(d["is_builtin"])
        self.assertEqual(d["created_at"], "2026-01-01T00:00:00")

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "template_id": "test-2",
            "name": "From Dict",
            "prompt_text": "some prompt",
            "is_builtin": False,
            "created_at": "2026-02-01T12:00:00",
        }
        t = PromptTemplate.from_dict(data)
        self.assertEqual(t.template_id, "test-2")
        self.assertEqual(t.name, "From Dict")
        self.assertEqual(t.prompt_text, "some prompt")
        self.assertFalse(t.is_builtin)

    def test_roundtrip(self):
        """Test serialization/deserialization roundtrip."""
        original = PromptTemplate(
            template_id="rt-1",
            name="Roundtrip",
            prompt_text="Extract key points from this.",
        )
        restored = PromptTemplate.from_dict(original.to_dict())
        self.assertEqual(original.template_id, restored.template_id)
        self.assertEqual(original.name, restored.name)
        self.assertEqual(original.prompt_text, restored.prompt_text)


class TestBuiltinTemplates(unittest.TestCase):
    """Tests for built-in templates."""

    def test_at_least_five_builtins(self):
        """Verify at least 5 built-in templates exist."""
        self.assertGreaterEqual(len(BUILTIN_TEMPLATES), 5)

    def test_builtin_names(self):
        """Verify expected built-in template names."""
        names = {t.name for t in BUILTIN_TEMPLATES}
        expected = {
            "Action Items",
            "Key Decisions",
            "Brief Summary",
            "Detailed Notes",
            "Meeting Minutes",
        }
        self.assertTrue(expected.issubset(names))

    def test_builtins_are_marked_builtin(self):
        """All built-in templates have is_builtin=True."""
        for t in BUILTIN_TEMPLATES:
            self.assertTrue(t.is_builtin, f"{t.name} should be builtin")

    def test_builtins_have_prompt_text(self):
        """All built-in templates have non-empty prompt text."""
        for t in BUILTIN_TEMPLATES:
            self.assertTrue(
                len(t.prompt_text.strip()) > 0,
                f"{t.name} has empty prompt_text",
            )


class TestPromptTemplateManager(unittest.TestCase):
    """Tests for the PromptTemplateManager class."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_file = self.temp_dir / "prompt_templates.json"
        self.manager = PromptTemplateManager(config_file=str(self.config_file))

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_get_all_templates_includes_builtins(self):
        """All built-in templates are returned."""
        all_templates = self.manager.get_all_templates()
        builtin_ids = {t.template_id for t in all_templates if t.is_builtin}
        expected_ids = {t.template_id for t in BUILTIN_TEMPLATES}
        self.assertEqual(builtin_ids, expected_ids)

    def test_get_builtin_templates(self):
        """get_builtin_templates returns only builtins."""
        builtins = self.manager.get_builtin_templates()
        self.assertEqual(len(builtins), len(BUILTIN_TEMPLATES))
        for t in builtins:
            self.assertTrue(t.is_builtin)

    def test_get_custom_templates_initially_empty(self):
        """No custom templates initially."""
        customs = self.manager.get_custom_templates()
        self.assertEqual(len(customs), 0)

    def test_save_custom_template(self):
        """Test saving a custom template."""
        template = self.manager.save_custom_template(
            "My Template", "Summarize briefly.",
        )
        self.assertFalse(template.is_builtin)
        self.assertEqual(template.name, "My Template")
        self.assertEqual(template.prompt_text, "Summarize briefly.")
        self.assertTrue(template.template_id.startswith("custom-"))

        # Verify it persists
        customs = self.manager.get_custom_templates()
        self.assertEqual(len(customs), 1)
        self.assertEqual(customs[0].name, "My Template")

    def test_save_custom_template_persists_to_file(self):
        """Custom templates are saved to disk."""
        self.manager.save_custom_template("Persistent", "prompt text")
        self.assertTrue(self.config_file.exists())

        with open(self.config_file) as f:
            data = json.load(f)
        self.assertEqual(len(data["templates"]), 1)
        self.assertEqual(data["templates"][0]["name"], "Persistent")

    def test_load_custom_templates_from_file(self):
        """Custom templates are loaded from disk on init."""
        self.manager.save_custom_template("Loaded", "prompt")
        # Create a new manager instance to test loading
        new_manager = PromptTemplateManager(config_file=str(self.config_file))
        customs = new_manager.get_custom_templates()
        self.assertEqual(len(customs), 1)
        self.assertEqual(customs[0].name, "Loaded")

    def test_delete_custom_template(self):
        """Test deleting a custom template."""
        template = self.manager.save_custom_template("ToDelete", "prompt")
        self.assertEqual(len(self.manager.get_custom_templates()), 1)

        result = self.manager.delete_custom_template(template.template_id)
        self.assertTrue(result)
        self.assertEqual(len(self.manager.get_custom_templates()), 0)

    def test_delete_nonexistent_template(self):
        """Deleting a non-existent template returns False."""
        result = self.manager.delete_custom_template("nonexistent-id")
        self.assertFalse(result)

    def test_cannot_delete_builtin_template(self):
        """Built-in templates cannot be deleted."""
        result = self.manager.delete_custom_template("action-items")
        self.assertFalse(result)

        # Verify it still exists
        template = self.manager.get_template("action-items")
        self.assertIsNotNone(template)

    def test_get_template_by_id(self):
        """Test getting a template by its ID."""
        # Built-in
        t = self.manager.get_template("action-items")
        self.assertIsNotNone(t)
        self.assertEqual(t.name, "Action Items")

        # Custom
        custom = self.manager.save_custom_template("Custom", "prompt")
        t2 = self.manager.get_template(custom.template_id)
        self.assertIsNotNone(t2)
        self.assertEqual(t2.name, "Custom")

    def test_get_template_nonexistent(self):
        """Getting a non-existent template returns None."""
        t = self.manager.get_template("does-not-exist")
        self.assertIsNone(t)

    def test_multiple_custom_templates(self):
        """Test saving multiple custom templates."""
        self.manager.save_custom_template("Template A", "prompt A")
        self.manager.save_custom_template("Template B", "prompt B")
        self.manager.save_custom_template("Template C", "prompt C")

        customs = self.manager.get_custom_templates()
        self.assertEqual(len(customs), 3)
        names = {t.name for t in customs}
        self.assertEqual(names, {"Template A", "Template B", "Template C"})

    def test_special_characters_in_template_name(self):
        """Templates with special characters in names work correctly."""
        t = self.manager.save_custom_template(
            "Template with 'quotes' & <special> chars!",
            "Some prompt",
        )
        retrieved = self.manager.get_template(t.template_id)
        self.assertEqual(
            retrieved.name,
            "Template with 'quotes' & <special> chars!",
        )

    def test_corrupt_config_file_handled(self):
        """Manager handles corrupt config file gracefully."""
        self.config_file.write_text("not valid json {{{{")
        manager = PromptTemplateManager(config_file=str(self.config_file))
        # Should still have builtins
        self.assertGreaterEqual(len(manager.get_all_templates()), 5)
        self.assertEqual(len(manager.get_custom_templates()), 0)


if __name__ == "__main__":
    unittest.main()
