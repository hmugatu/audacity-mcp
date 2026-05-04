"""
tracks.py — Track inspection and selection tools.

Audacity scripting commands:
  GetInfo: Type=Tracks   → JSON array of track dicts
  GetInfo: Type=Selection → JSON dict with start/end/tracks
  SelectTime: Start=N End=N RelativeTo=ProjectStart
  SelectTracks: Track=N TrackCount=1 Mode=Set
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _parse_json_response(response: str) -> Any:
    """Extract the JSON payload from a GetInfo response (first line)."""
    first_line = response.split("\n")[0].strip()
    if not first_line or first_line.startswith("BatchCommand"):
        return None
    return json.loads(first_line)


def get_tracks(conn) -> list[dict]:
    """Return a list of all tracks in the current project."""
    response = conn.send_command("GetInfo: Type=Tracks")
    result   = _parse_json_response(response)
    return result if isinstance(result, list) else []


def get_selection(conn) -> dict:
    """Return the current time selection as {start, end, tracks}."""
    response = conn.send_command("GetInfo: Type=Selection")
    result   = _parse_json_response(response)
    return result if isinstance(result, dict) else {}


def select_time(conn, start: float, end: float) -> None:
    """Set the time selection from `start` to `end` seconds."""
    conn.send_command(f"SelectTime: Start={start} End={end} RelativeTo=ProjectStart")
    logger.info("Selected time %.3f → %.3f", start, end)


def select_tracks(conn, track_index: int) -> None:
    """Select a single track by 0-based index."""
    conn.send_command(f"SelectTracks: Track={track_index} TrackCount=1 Mode=Set")
    logger.info("Selected track %d", track_index)
