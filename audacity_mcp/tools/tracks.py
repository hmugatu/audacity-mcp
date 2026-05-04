"""
tracks.py — Track inspection and selection tools.

Audacity scripting commands:
  GetInfo: Type=Tracks   → JSON array of track dicts
  GetInfo: Type=Selection → JSON dict with start/end/tracks
  SelectTime: Start=N End=N RelativeTo=ProjectStart
  SelectTracks: Track=N TrackCount=1 Mode=Set
"""

import logging

from audacity_mcp.tools._utils import parse_json_response

logger = logging.getLogger(__name__)


def get_tracks(conn) -> list[dict]:
    """Return a list of all tracks in the current project."""
    response = conn.send_command("GetInfo: Type=Tracks")
    result   = parse_json_response(response)
    return result if isinstance(result, list) else []


def get_selection(conn) -> dict:
    """Return the current time selection as {start, end, tracks}."""
    response = conn.send_command("GetInfo: Type=Selection")
    result   = parse_json_response(response)
    return result if isinstance(result, dict) else {}


def select_time(conn, start: float, end: float) -> None:
    """Set the time selection from `start` to `end` seconds."""
    conn.send_command(f"SelectTime: Start={start} End={end} RelativeTo=ProjectStart")
    logger.info("Selected time %.3f → %.3f", start, end)


def select_tracks(conn, track_index: int) -> None:
    """Select a single track by 0-based index."""
    conn.send_command(f"SelectTracks: Track={track_index} TrackCount=1 Mode=Set")
    logger.info("Selected track %d", track_index)
