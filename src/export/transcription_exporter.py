"""
Transcription export in multiple formats for ScribeVault.

Supports plain text (.txt), markdown (.md), and SRT subtitle (.srt) formats.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from utils import format_duration, parse_datetime

logger = logging.getLogger(__name__)

SIZE_WARNING_THRESHOLD = 50 * 1024  # 50KB


class TranscriptionExportError(Exception):
    """Custom exception for transcription export errors."""
    pass


class TranscriptionExporter:
    """Exports transcription data in multiple formats."""

    def __init__(self, recording_data: Dict[str, Any]):
        """Initialize with recording data dict.

        Args:
            recording_data: Dict with keys like title, transcription,
                created_at, duration, category, etc.
        """
        self.data = recording_data
        self.title = (
            recording_data.get('title')
            or recording_data.get('filename', 'Untitled')
        )
        self.transcription = recording_data.get('transcription', '')
        self.duration = recording_data.get('duration', 0)
        self.category = recording_data.get('category', 'other')
        self.created_at = recording_data.get('created_at', '')
        self.segments = recording_data.get('segments', [])

    def needs_size_warning(self) -> bool:
        """Check if transcription exceeds the size warning threshold."""
        text_size = len(self.transcription.encode('utf-8'))
        return text_size > SIZE_WARNING_THRESHOLD

    def get_transcription_size(self) -> int:
        """Return transcription size in bytes."""
        return len(self.transcription.encode('utf-8'))

    def _extract_speakers(self) -> List[str]:
        """Extract unique speaker labels from transcription text.

        Looks for patterns like "Speaker 1:", "John:", etc. at
        the start of lines.
        """
        speakers = []
        for line in self.transcription.splitlines():
            stripped = line.strip()
            if ':' in stripped:
                label = stripped.split(':', 1)[0].strip()
                if label and len(label) < 50 and label not in speakers:
                    # Heuristic: speaker labels are short, at line start
                    # Exclude lines that look like timestamps or metadata
                    if not any(c.isdigit() and '-' in label for c in label):
                        speakers.append(label)
        return speakers

    def _build_metadata_header_txt(self) -> str:
        """Build a plain text metadata header."""
        lines = []
        lines.append(f"Title: {self.title}")

        dt = parse_datetime(self.created_at)
        if dt:
            lines.append(f"Date: {dt.strftime('%Y-%m-%d %H:%M:%S')}")

        if self.duration and self.duration > 0:
            lines.append(f"Duration: {format_duration(self.duration, style="descriptive")}")

        if self.category and self.category != 'other':
            lines.append(f"Category: {self.category.title()}")

        speakers = self._extract_speakers()
        if speakers:
            lines.append(f"Speakers: {', '.join(speakers)}")

        return '\n'.join(lines)

    def _build_metadata_header_md(self) -> str:
        """Build a markdown metadata header."""
        lines = []
        lines.append(f"# {self.title}")
        lines.append("")

        dt = parse_datetime(self.created_at)
        if dt:
            lines.append(
                f"**Date**: {dt.strftime('%Y-%m-%d %H:%M:%S')}  "
            )

        if self.duration and self.duration > 0:
            lines.append(
                f"**Duration**: {format_duration(self.duration, style="descriptive")}  "
            )

        if self.category and self.category != 'other':
            lines.append(f"**Category**: {self.category.title()}  ")

        speakers = self._extract_speakers()
        if speakers:
            lines.append(f"**Speakers**: {', '.join(speakers)}  ")

        lines.append(
            f"**Exported**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        return '\n'.join(lines)

    def export_txt(self, output_path: Path) -> Path:
        """Export transcription as plain text.

        Args:
            output_path: Path to write the .txt file.

        Returns:
            The path written to.
        """
        output_path = Path(output_path)

        header = self._build_metadata_header_txt()
        separator = "=" * 60

        content = f"{header}\n{separator}\n\n{self.transcription}\n"

        try:
            output_path.write_text(content, encoding='utf-8')
            logger.info(f"TXT export saved: {output_path}")
            return output_path
        except OSError as e:
            raise TranscriptionExportError(
                f"Failed to write TXT export: {e}"
            )

    def export_markdown(self, output_path: Path) -> Path:
        """Export transcription as markdown.

        Args:
            output_path: Path to write the .md file.

        Returns:
            The path written to.
        """
        output_path = Path(output_path)

        header = self._build_metadata_header_md()

        content = f"""{header}

---

## Transcription

{self.transcription}

---

*Exported by ScribeVault*
"""

        try:
            output_path.write_text(content, encoding='utf-8')
            logger.info(f"Markdown export saved: {output_path}")
            return output_path
        except OSError as e:
            raise TranscriptionExportError(
                f"Failed to write markdown export: {e}"
            )

    def has_timestamps(self) -> bool:
        """Check if timestamp/segment data is available."""
        return bool(self.segments)

    def export_srt(self, output_path: Path) -> Path:
        """Export transcription as SRT subtitle format.

        Requires segment data with 'start' and 'end' timestamps.

        Args:
            output_path: Path to write the .srt file.

        Returns:
            The path written to.

        Raises:
            TranscriptionExportError: If no timestamp data is available.
        """
        output_path = Path(output_path)

        if not self.has_timestamps():
            raise TranscriptionExportError(
                "No timestamp data available for SRT export. "
                "SRT format requires segment timestamps."
            )

        lines = []
        counter = 0
        for segment in self.segments:
            start = segment.get('start', 0)
            end = segment.get('end', 0)
            text = segment.get('text', '').strip()
            if not text:
                continue

            counter += 1
            lines.append(str(counter))
            lines.append(
                f"{self._srt_timestamp(start)} --> "
                f"{self._srt_timestamp(end)}"
            )
            lines.append(text)
            lines.append("")

        content = '\n'.join(lines)

        try:
            output_path.write_text(content, encoding='utf-8')
            logger.info(f"SRT export saved: {output_path}")
            return output_path
        except OSError as e:
            raise TranscriptionExportError(
                f"Failed to write SRT export: {e}"
            )

    @staticmethod
    def _srt_timestamp(seconds: float) -> str:
        """Convert seconds to SRT timestamp format HH:MM:SS,mmm."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
