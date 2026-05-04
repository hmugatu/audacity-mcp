"""
export.py — Audio export and import tools.

Audacity infers the output format from the file extension:
  .wav  → PCM WAV
  .mp3  → MP3 (requires LAME encoder)
  .flac → FLAC
  .aiff → AIFF
  .ogg  → Ogg Vorbis
"""

import logging

logger = logging.getLogger(__name__)


def export_audio(conn, path: str, channels: int = 2) -> None:
    """Export the entire project to a file. Format inferred from extension."""
    conn.send_command(f"Export2: Filename={path} Numchannels={channels}")
    logger.info("Exported project → %s", path)


def export_selection(conn, path: str, channels: int = 2) -> None:
    """Export the current time selection to a file."""
    conn.send_command(f"ExportSel2: Filename={path} Numchannels={channels}")
    logger.info("Exported selection → %s", path)


def import_audio(conn, path: str) -> None:
    """Import an audio file into the current project as a new track."""
    conn.send_command(f"Import2: Filename={path}")
    logger.info("Imported %s", path)
