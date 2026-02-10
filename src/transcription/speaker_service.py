"""
Speaker management service for ScribeVault.

Handles parsing, renaming, and inserting speaker labels in transcription text.
Speaker-labeled transcriptions use the format:
    Speaker 1: Hello, how are you?
    Speaker 2: I'm fine, thanks.
"""

import re
import logging
from typing import List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Pattern matching "SpeakerName: text" at start of a line
SPEAKER_PATTERN = re.compile(r'^([^:\n]+?):\s', re.MULTILINE)


@dataclass
class SpeakerSegment:
    """A segment of transcription attributed to a speaker."""
    speaker: str
    text: str
    start_pos: int
    end_pos: int


def parse_speakers(transcription: str) -> List[str]:
    """Extract unique speaker names from a transcription.

    Args:
        transcription: The full transcription text.

    Returns:
        List of unique speaker names in order of first appearance.
    """
    if not transcription or not transcription.strip():
        return []

    seen = set()
    speakers = []
    for match in SPEAKER_PATTERN.finditer(transcription):
        name = match.group(1).strip()
        if name and name not in seen:
            seen.add(name)
            speakers.append(name)
    return speakers


def parse_segments(transcription: str) -> List[SpeakerSegment]:
    """Parse transcription into speaker segments.

    Each segment contains the speaker name, the text they spoke,
    and the character positions in the original string.

    Args:
        transcription: The full transcription text.

    Returns:
        List of SpeakerSegment objects.
    """
    if not transcription or not transcription.strip():
        return []

    segments: List[SpeakerSegment] = []
    matches = list(SPEAKER_PATTERN.finditer(transcription))

    if not matches:
        # No speaker labels found — entire text is one unlabeled segment
        return [SpeakerSegment(
            speaker="",
            text=transcription,
            start_pos=0,
            end_pos=len(transcription),
        )]

    # Text before the first speaker label (if any)
    if matches[0].start() > 0:
        prefix = transcription[:matches[0].start()].rstrip('\n')
        if prefix.strip():
            segments.append(SpeakerSegment(
                speaker="",
                text=prefix,
                start_pos=0,
                end_pos=matches[0].start(),
            ))

    for i, match in enumerate(matches):
        speaker = match.group(1).strip()
        text_start = match.end()

        # Text runs until the next speaker label or end of string
        if i + 1 < len(matches):
            text_end = matches[i + 1].start()
        else:
            text_end = len(transcription)

        text = transcription[text_start:text_end].strip()
        segments.append(SpeakerSegment(
            speaker=speaker,
            text=text,
            start_pos=match.start(),
            end_pos=text_end,
        ))

    return segments


def rename_speaker(
    transcription: str,
    old_name: str,
    new_name: str,
) -> str:
    """Rename all occurrences of a speaker in the transcription.

    Performs exact replacement of the speaker label prefix, preserving
    the rest of the text.

    Args:
        transcription: The full transcription text.
        old_name: Current speaker name to replace.
        new_name: New speaker name.

    Returns:
        Updated transcription with the speaker renamed.
    """
    if not transcription or not old_name or not new_name:
        return transcription or ""

    if old_name == new_name:
        return transcription

    # Replace "OldName: " with "NewName: " at line beginnings
    pattern = re.compile(
        r'^(' + re.escape(old_name) + r'):\s',
        re.MULTILINE,
    )
    return pattern.sub(f'{new_name}: ', transcription)


def insert_speaker_label(
    transcription: str,
    position: int,
    speaker_name: str,
) -> str:
    """Insert a speaker label at a given character position.

    The label is inserted as "\\nSpeakerName: " to start a new
    speaker segment at the specified position.

    Args:
        transcription: The full transcription text.
        position: Character index where the label should be inserted.
        speaker_name: Name of the speaker to insert.

    Returns:
        Updated transcription with the new speaker label.
    """
    if not speaker_name:
        return transcription or ""

    if not transcription:
        return f"{speaker_name}: "

    position = max(0, min(position, len(transcription)))

    label = f"\n{speaker_name}: "

    return transcription[:position] + label + transcription[position:]


def insert_speaker_at_line(
    transcription: str,
    line_number: int,
    speaker_name: str,
) -> str:
    """Insert a speaker label at the beginning of a specific line.

    Args:
        transcription: The full transcription text.
        line_number: Zero-based line index.
        speaker_name: Name of the speaker to insert.

    Returns:
        Updated transcription with the new speaker label.
    """
    if not transcription or not speaker_name:
        return transcription or ""

    lines = transcription.split('\n')
    line_number = max(0, min(line_number, len(lines) - 1))

    line = lines[line_number]
    # If the line already has a speaker label, replace it
    match = SPEAKER_PATTERN.match(line)
    if match:
        lines[line_number] = f"{speaker_name}: {line[match.end():]}"
    else:
        lines[line_number] = f"{speaker_name}: {line}"

    return '\n'.join(lines)


def build_transcription(segments: List[Tuple[str, str]]) -> str:
    """Build a transcription string from speaker-text pairs.

    Args:
        segments: List of (speaker_name, text) tuples.

    Returns:
        Formatted transcription string.
    """
    lines = []
    for speaker, text in segments:
        if speaker:
            lines.append(f"{speaker}: {text}")
        else:
            lines.append(text)
    return '\n'.join(lines)


def has_speaker_labels(transcription: str) -> bool:
    """Check if the transcription contains any speaker labels.

    Args:
        transcription: The transcription text.

    Returns:
        True if speaker labels are detected.
    """
    if not transcription:
        return False
    return bool(SPEAKER_PATTERN.search(transcription))
