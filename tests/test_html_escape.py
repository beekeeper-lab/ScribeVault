"""
Unit tests for HTML escaping in summary viewer (BEAN-028).

Tests the _format_diarized_html logic directly to avoid
PySide6 import dependency in CI/test environments.
"""

import html
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def _format_diarized_html(diarized_text: str) -> str:
    """Standalone copy of SummaryViewerDialog._format_diarized_html.

    Mirrors the production code to validate escaping behavior
    without requiring PySide6.
    """
    speaker_colors = [
        "#58a6ff", "#f78166", "#7ee787",
        "#d2a8ff", "#ff7b72", "#79c0ff",
    ]
    speaker_color_map = {}
    color_idx = 0

    lines = diarized_text.strip().split("\n")
    html_parts = [
        '<div style="font-family: Segoe UI, Arial,'
        " sans-serif; font-size: 13px;"
        ' line-height: 1.6; color: #ffffff;">'
    ]

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = re.match(r"^(Speaker\s+\d+):\s*(.*)", line)
        if match:
            speaker = html.escape(match.group(1))
            text = html.escape(match.group(2))

            if speaker not in speaker_color_map:
                speaker_color_map[speaker] = speaker_colors[
                    color_idx % len(speaker_colors)
                ]
                color_idx += 1

            color = speaker_color_map[speaker]
            html_parts.append(
                f'<p style="margin: 6px 0;">'
                f'<b style="color: {color};">'
                f"{speaker}:</b> {text}"
                f"</p>"
            )
        else:
            html_parts.append(
                f'<p style="margin: 6px 0;">'
                f"{html.escape(line)}</p>"
            )

    html_parts.append("</div>")
    return "".join(html_parts)


class TestDiarizedHtmlEscaping(unittest.TestCase):
    """Test that _format_diarized_html escapes dynamic content."""

    def test_angle_brackets_escaped(self):
        """Text with <script> should render as literal text."""
        result = _format_diarized_html(
            "Speaker 1: <script>alert('xss')</script>"
        )
        self.assertNotIn("<script>", result)
        self.assertIn("&lt;script&gt;", result)

    def test_ampersand_escaped(self):
        """Text with & should be escaped to &amp;."""
        result = _format_diarized_html("Speaker 1: Tom & Jerry")
        self.assertIn("Tom &amp; Jerry", result)

    def test_quotes_escaped(self):
        """Text with quotes should be escaped."""
        result = _format_diarized_html(
            'Speaker 1: He said "hello"'
        )
        self.assertIn("&quot;hello&quot;", result)

    def test_img_onerror_escaped(self):
        """Img tag with onerror should be escaped."""
        result = _format_diarized_html(
            'Speaker 1: <img onerror="alert(1)" src=x>'
        )
        self.assertNotIn("<img", result)
        self.assertIn("&lt;img", result)

    def test_non_speaker_line_escaped(self):
        """Non-speaker lines should also be escaped."""
        result = _format_diarized_html("<b>bold injection</b>")
        self.assertNotIn("<b>bold", result)
        self.assertIn("&lt;b&gt;bold", result)

    def test_normal_text_unchanged(self):
        """Normal text without special characters renders correctly."""
        result = _format_diarized_html("Speaker 1: Hello world")
        self.assertIn("Hello world", result)


if __name__ == '__main__':
    unittest.main()
