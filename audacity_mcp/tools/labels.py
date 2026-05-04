"""
labels.py — Label track tools.
"""

import logging

from audacity_mcp.tools._utils import parse_json_response

logger = logging.getLogger(__name__)


def add_label(conn, time: float, text: str) -> None:
    """Add a point label at `time` seconds with the given text."""
    conn.send_command(f'AddLabelAt: SelectedText="{text}" Start={time}')
    logger.info("Added label '%s' at %.3f", text, time)


def get_labels(conn) -> list[dict]:
    """Return all labels as a list of dicts with keys: start, end, title."""
    response = conn.send_command("GetInfo: Type=Labels")
    result   = parse_json_response(response)
    return result if isinstance(result, list) else []


def export_labels(conn, path: str) -> None:
    """Export the label track to a tab-separated .txt file."""
    conn.send_command(f"ExportLabels: Filename={path}")
    logger.info("Exported labels → %s", path)
