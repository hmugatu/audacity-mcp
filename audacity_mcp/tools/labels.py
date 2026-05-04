"""
labels.py — Label track tools.
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _parse_json_response(response: str) -> Any:
    first_line = response.split("\n")[0].strip()
    if not first_line or first_line.startswith("BatchCommand"):
        return None
    return json.loads(first_line)


def add_label(conn, time: float, text: str) -> None:
    """Add a point label at `time` seconds with the given text."""
    conn.send_command(f"AddLabelAt: SelectedText={text} Start={time}")
    logger.info("Added label '%s' at %.3f", text, time)


def get_labels(conn) -> list[dict]:
    """Return all labels as a list of dicts with keys: start, end, title."""
    response = conn.send_command("GetInfo: Type=Labels")
    result   = _parse_json_response(response)
    return result if isinstance(result, list) else []


def export_labels(conn, path: str) -> None:
    """Export the label track to a tab-separated .txt file."""
    conn.send_command(f"ExportLabels: Filename={path}")
    logger.info("Exported labels → %s", path)
