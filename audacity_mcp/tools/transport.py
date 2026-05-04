"""transport.py — Playback and project state tools."""

import logging

logger = logging.getLogger(__name__)


def play(conn) -> None:
    """Start playback from the current cursor position."""
    conn.send_command("Play:")


def stop(conn) -> None:
    """Stop playback."""
    conn.send_command("Stop:")


def rewind(conn) -> None:
    """Move the playhead to the start of the project."""
    conn.send_command("CursProjectStart:")


def undo(conn) -> None:
    """Undo the last action."""
    conn.send_command("Undo:")
