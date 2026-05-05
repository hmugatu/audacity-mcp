"""
server.py — FastMCP entry point for audacity-mcp.

Run via:
    uvx --from /path/to/audacity-mcp audacity-mcp

Or add to Claude Desktop's claude_desktop_config.json:
    {
      "mcpServers": {
        "audacity": {
          "command": "uvx",
          "args": ["--from", "git+https://github.com/jeffshoemaker/audacity-mcp", "audacity-mcp"]
        }
      }
    }

Audacity must be running with mod-script-pipe enabled before connecting.
"""

import logging

from mcp.server.fastmcp import FastMCP

from audacity_mcp.client import AudacityConnection
from audacity_mcp.tools import effects, export, labels, tracks, transport

logging.basicConfig(level=logging.WARNING, format="%(message)s")

mcp  = FastMCP("audacity-mcp")
conn = AudacityConnection()


def get_audacity_connection() -> AudacityConnection:
    """Return the global connection, connecting on first use."""
    if not conn._connected:
        try:
            conn.connect()
        except ConnectionError as exc:
            raise RuntimeError(
                "Cannot connect to Audacity. "
                "Make sure Audacity is running with mod-script-pipe enabled.\n"
                f"Details: {exc}"
            ) from exc
    return conn


# ── Track tools ───────────────────────────────────────────────────────────────

@mcp.tool()
def get_tracks() -> list[dict]:
    """List all tracks in the current Audacity project."""
    return tracks.get_tracks(get_audacity_connection())


@mcp.tool()
def get_selection() -> dict:
    """Return the current time selection as {start, end, tracks}."""
    return tracks.get_selection(get_audacity_connection())


@mcp.tool()
def select_time(start: float, end: float) -> str:
    """Set the time selection from start to end (seconds)."""
    tracks.select_time(get_audacity_connection(), start=start, end=end)
    return f"Selected {start:.3f}s → {end:.3f}s"


@mcp.tool()
def select_tracks(track_index: int) -> str:
    """Select a single track by 0-based index."""
    tracks.select_tracks(get_audacity_connection(), track_index=track_index)
    return f"Selected track {track_index}"


# ── Effect tools ──────────────────────────────────────────────────────────────

@mcp.tool()
def normalize(peak_db: float = -1.0) -> str:
    """Normalize the current selection to peak_db dBFS (default -1.0)."""
    effects.normalize(get_audacity_connection(), peak_db=peak_db)
    return f"Normalized to {peak_db} dBFS"


@mcp.tool()
def amplify(db: float) -> str:
    """Amplify the current selection by db decibels."""
    effects.amplify(get_audacity_connection(), db=db)
    return f"Amplified by {db} dB"


@mcp.tool()
def fade_in() -> str:
    """Apply a linear fade-in over the current selection."""
    effects.fade_in(get_audacity_connection())
    return "Fade-in applied"


@mcp.tool()
def fade_out() -> str:
    """Apply a linear fade-out over the current selection."""
    effects.fade_out(get_audacity_connection())
    return "Fade-out applied"


@mcp.tool()
def noise_reduction_profile() -> str:
    """
    Step 1: Capture a noise profile from the current selection.
    Select a region of pure background noise before calling this.
    """
    effects.noise_reduction_profile(get_audacity_connection())
    return "Noise profile captured. Now select the full audio and call noise_reduction_apply."


@mcp.tool()
def noise_reduction_apply(
    level: int = 12,
    sensitivity: float = 6.0,
    frequency: int = 3,
) -> str:
    """
    Step 2: Apply the captured noise profile to the current selection.
    Call noise_reduction_profile first on a noise-only region.
    """
    effects.noise_reduction_apply(
        get_audacity_connection(),
        level=level,
        sensitivity=sensitivity,
        frequency=frequency,
    )
    return "Noise reduction applied"


@mcp.tool()
def apply_macro(macro_name: str) -> str:
    """Run a saved Audacity macro by name (Tools → Macros in Audacity)."""
    effects.apply_macro(get_audacity_connection(), macro_name=macro_name)
    return f"Macro '{macro_name}' applied"


# ── Export / import tools ─────────────────────────────────────────────────────

@mcp.tool()
def export_audio(path: str, channels: int = 2) -> str:
    """
    Export the full project to a file. Format inferred from extension.
    Supported: .wav .flac .mp3 .aiff .ogg
    """
    export.export_audio(get_audacity_connection(), path=path, channels=channels)
    return f"Exported → {path}"


@mcp.tool()
def export_selection(path: str, channels: int = 2) -> str:
    """Export the current time selection to a file."""
    export.export_selection(get_audacity_connection(), path=path, channels=channels)
    return f"Exported selection → {path}"


@mcp.tool()
def import_audio(path: str) -> str:
    """Import an audio file into the project as a new track."""
    export.import_audio(get_audacity_connection(), path=path)
    return f"Imported {path}"


# ── Label tools ───────────────────────────────────────────────────────────────

@mcp.tool()
def add_label(time: float, text: str) -> str:
    """Add a point label at the given time (seconds) with the given text."""
    labels.add_label(get_audacity_connection(), time=time, text=text)
    return f"Label '{text}' added at {time:.3f}s"


@mcp.tool()
def get_labels() -> list[dict]:
    """Return all labels in the project."""
    return labels.get_labels(get_audacity_connection())


@mcp.tool()
def export_labels(path: str) -> str:
    """Export the label track to a tab-separated .txt file."""
    labels.export_labels(get_audacity_connection(), path=path)
    return f"Labels exported → {path}"


# ── Transport tools ───────────────────────────────────────────────────────────

@mcp.tool()
def play() -> str:
    """Start Audacity playback."""
    transport.play(get_audacity_connection())
    return "Playback started"


@mcp.tool()
def stop() -> str:
    """Stop Audacity playback."""
    transport.stop(get_audacity_connection())
    return "Playback stopped"


@mcp.tool()
def rewind() -> str:
    """Move the playhead to the start of the project."""
    transport.rewind(get_audacity_connection())
    return "Rewound to project start"


@mcp.tool()
def undo() -> str:
    """Undo the last action in Audacity."""
    transport.undo(get_audacity_connection())
    return "Undone"


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    mcp.run()


if __name__ == "__main__":
    main()
