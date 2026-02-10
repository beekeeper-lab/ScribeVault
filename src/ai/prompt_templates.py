"""
Prompt template management for ScribeVault summary re-generation.
"""

import json
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PromptTemplate:
    """Represents a single prompt template."""

    def __init__(
        self,
        template_id: str,
        name: str,
        prompt_text: str,
        is_builtin: bool = False,
        created_at: Optional[str] = None,
    ):
        self.template_id = template_id
        self.name = name
        self.prompt_text = prompt_text
        self.is_builtin = is_builtin
        self.created_at = created_at or datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "prompt_text": self.prompt_text,
            "is_builtin": self.is_builtin,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptTemplate":
        """Deserialize from dictionary."""
        return cls(
            template_id=data["template_id"],
            name=data["name"],
            prompt_text=data["prompt_text"],
            is_builtin=data.get("is_builtin", False),
            created_at=data.get("created_at"),
        )


# Built-in prompt templates
BUILTIN_TEMPLATES = [
    PromptTemplate(
        template_id="action-items",
        name="Action Items",
        prompt_text=(
            "You are an assistant that extracts action "
            "items from transcripts. "
            "Analyze the following transcript and produce "
            "a clear, numbered list "
            "of action items. For each item, include WHO "
            "is responsible and WHAT "
            "they need to do. If deadlines are mentioned, include them. "
            "Format the output as a numbered list."
        ),
        is_builtin=True,
        created_at="2026-01-01T00:00:00",
    ),
    PromptTemplate(
        template_id="key-decisions",
        name="Key Decisions",
        prompt_text=(
            "You are an assistant that identifies key "
            "decisions from transcripts. "
            "Analyze the following transcript and extract "
            "all decisions that were "
            "made. For each decision, note the context, "
            "the decision itself, and "
            "any conditions or caveats mentioned. "
            "Format as a structured list with clear headers."
        ),
        is_builtin=True,
        created_at="2026-01-01T00:00:00",
    ),
    PromptTemplate(
        template_id="brief-summary",
        name="Brief Summary",
        prompt_text=(
            "You are an assistant that creates brief, concise summaries. "
            "Summarize the following transcript in 3-5 sentences, capturing "
            "only the most essential points. Be direct and avoid unnecessary "
            "detail."
        ),
        is_builtin=True,
        created_at="2026-01-01T00:00:00",
    ),
    PromptTemplate(
        template_id="detailed-notes",
        name="Detailed Notes",
        prompt_text=(
            "You are an assistant that creates comprehensive, detailed notes "
            "from transcripts. Organize the content into "
            "logical sections with "
            "headers. Include all significant points, examples, and context. "
            "Use bullet points for clarity. Preserve important quotes or "
            "specific figures mentioned."
        ),
        is_builtin=True,
        created_at="2026-01-01T00:00:00",
    ),
    PromptTemplate(
        template_id="meeting-minutes",
        name="Meeting Minutes",
        prompt_text=(
            "You are an assistant that creates professional meeting minutes. "
            "Structure the output with these sections:\n"
            "- **Attendees**: List people mentioned\n"
            "- **Agenda Items**: Topics discussed\n"
            "- **Discussion Summary**: Key points for each topic\n"
            "- **Decisions Made**: Any decisions reached\n"
            "- **Action Items**: Tasks assigned with owners\n"
            "- **Next Steps**: Follow-up items and next meeting topics\n"
            "Use a professional, factual tone."
        ),
        is_builtin=True,
        created_at="2026-01-01T00:00:00",
    ),
]


class PromptTemplateManager:
    """Manages built-in and custom prompt templates."""

    def __init__(self, config_file: str = "config/prompt_templates.json"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(exist_ok=True)
        self._builtin_templates = {t.template_id: t for t in BUILTIN_TEMPLATES}
        self._custom_templates: Dict[str, PromptTemplate] = {}
        self._load_custom_templates()

    def _load_custom_templates(self):
        """Load custom templates from config file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                for item in data.get("templates", []):
                    template = PromptTemplate.from_dict(item)
                    self._custom_templates[template.template_id] = template
            except Exception as e:
                logger.error(f"Error loading custom templates: {e}")

    def _save_custom_templates(self):
        """Save custom templates to config file."""
        try:
            templates = [t.to_dict() for t in self._custom_templates.values()]
            data = {"templates": templates}
            with open(self.config_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving custom templates: {e}")

    def get_all_templates(self) -> List[PromptTemplate]:
        """Get all templates (built-in first, then custom)."""
        builtin = sorted(
            self._builtin_templates.values(),
            key=lambda t: t.name,
        )
        custom = sorted(self._custom_templates.values(), key=lambda t: t.name)
        return builtin + custom

    def get_builtin_templates(self) -> List[PromptTemplate]:
        """Get only built-in templates."""
        return sorted(self._builtin_templates.values(), key=lambda t: t.name)

    def get_custom_templates(self) -> List[PromptTemplate]:
        """Get only custom templates."""
        return sorted(self._custom_templates.values(), key=lambda t: t.name)

    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Get a template by ID."""
        if template_id in self._builtin_templates:
            return self._builtin_templates[template_id]
        return self._custom_templates.get(template_id)

    def save_custom_template(
        self,
        name: str,
        prompt_text: str,
    ) -> PromptTemplate:
        """Save a new custom template.

        Args:
            name: Display name for the template
            prompt_text: The prompt text

        Returns:
            The created PromptTemplate
        """
        template_id = f"custom-{uuid.uuid4().hex[:12]}"
        template = PromptTemplate(
            template_id=template_id,
            name=name,
            prompt_text=prompt_text,
            is_builtin=False,
        )
        self._custom_templates[template_id] = template
        self._save_custom_templates()
        logger.info(f"Saved custom template: {name} ({template_id})")
        return template

    def delete_custom_template(self, template_id: str) -> bool:
        """Delete a custom template. Built-in templates cannot be deleted.

        Args:
            template_id: The template ID to delete

        Returns:
            True if deleted, False if not found or is built-in
        """
        if template_id in self._builtin_templates:
            logger.warning(f"Cannot delete built-in template: {template_id}")
            return False
        if template_id in self._custom_templates:
            del self._custom_templates[template_id]
            self._save_custom_templates()
            logger.info(f"Deleted custom template: {template_id}")
            return True
        return False
