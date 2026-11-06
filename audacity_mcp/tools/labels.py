"""
labels.py — Label track tools.

GetInfo: Type=Labels returns one entry per label track:
  [ [track_index, [ [start, end, "text"], ... ]], ... ]

SetLabel's Label=N counts labels across all label tracks in that order.
"""

import logging

from audacity_mcp.tools._utils import parse_json_response, quote

logger = logging.getLogger(__name__)


def _label_rows(conn) -> list[list]:
    """All labels as [track, start, end, text], in SetLabel index order."""
    result = parse_json_response(conn.send_command("GetInfo: Type=Labels"))
    rows = []
    for track, labels in result or []:
        for start, end, text in labels:
            rows.append([track, start, end, text])
    return rows


def add_label(conn, time: float, text: str, end: float | None = None) -> None:
    """
    Add a label at `time` seconds (a region label if `end` is given).

    Uses the current label track, or creates one. Moves the time selection
    to the label.
    """
    end = time if end is None else end
    conn.send_command(f"SelectTime: Start={time} End={end} RelativeTo=ProjectStart")
    before = _label_rows(conn)
    conn.send_command("AddLabel:")
    after = _label_rows(conn)

    # The new label's global index is the one position whose removal
    # gives back the previous list.
    index = next(
        (i for i in range(len(after)) if after[:i] + after[i + 1:] == before),
        None,
    )
    if index is None:
        raise RuntimeError("AddLabel did not create a label; is a project open?")
    if text:
        conn.send_command(f"SetLabel: Label={index} Text={quote(text)}")
    logger.info("Added label '%s' at %.3f", text, time)


def get_labels(conn) -> list[dict]:
    """Return all labels as dicts with keys: track, start, end, text."""
    return [
        {"track": track, "start": start, "end": end, "text": text}
        for track, start, end, text in _label_rows(conn)
    ]


def export_labels(conn, path: str) -> int:
    """
    Write all labels to a tab-separated .txt file in Audacity's label format
    (start, end, text). Returns the number of labels written.

    Audacity's ExportLabels command opens a file dialog, which blocks the
    pipe, so the file is written here from GetInfo instead. The path is on
    the machine running this server.
    """
    rows = _label_rows(conn)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for _track, start, end, text in rows:
            f.write(f"{start:.6f}\t{end:.6f}\t{text}\n")
    logger.info("Exported %d labels → %s", len(rows), path)
    return len(rows)
