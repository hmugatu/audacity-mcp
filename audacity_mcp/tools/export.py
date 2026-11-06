"""
export.py — Audio export and import tools.

Audacity infers the output format from the file extension:
  .wav  → PCM WAV
  .mp3  → MP3 (requires LAME encoder)
  .flac → FLAC
  .aiff → AIFF
  .ogg  → Ogg Vorbis

Export2 always exports the *current selection* (Audacity 3.x,
src/commands/ImportExportCommands.cpp), so export_audio selects everything
first. Audacity defaults to mono, so the channel count is always sent.

The selection uses the scriptable Select command, not the SelectAll menu
command: right after AddLabel the new label is in text-edit mode and
swallows SelectAll, which would export only part of the project. Select
needs the exact track count; an out-of-range TrackCount opens a modal
dialog that blocks the pipe.
"""

import logging

from audacity_mcp.tools._utils import parse_json_response, quote_path

logger = logging.getLogger(__name__)


def select_whole_project(conn) -> None:
    """Select every track over the whole project length."""
    track_list = parse_json_response(conn.send_command("GetInfo: Type=Tracks")) or []
    if not track_list:
        raise RuntimeError("The project has no tracks to export.")
    conn.send_command(
        f"Select: Start=0 End=0 RelativeTo=Project Track=0 "
        f"TrackCount={len(track_list)} Mode=Set"
    )


def export_audio(conn, path: str, channels: int = 2) -> None:
    """Export the entire project to a file (selects all first). Format inferred from extension."""
    select_whole_project(conn)
    conn.send_command(f"Export2: Filename={quote_path(path)} NumChannels={channels}")
    logger.info("Exported project → %s", path)


def export_selection(conn, path: str, channels: int = 2) -> None:
    """Export the current time selection to a file."""
    conn.send_command(f"Export2: Filename={quote_path(path)} NumChannels={channels}")
    logger.info("Exported selection → %s", path)


def import_audio(conn, path: str) -> None:
    """Import an audio file into the current project as a new track."""
    conn.send_command(f"Import2: Filename={quote_path(path)}")
    logger.info("Imported %s", path)
