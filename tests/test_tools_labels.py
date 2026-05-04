import json
import pytest
from unittest.mock import MagicMock
from audacity_mcp.tools.labels import add_label, get_labels, export_labels


def make_conn(response: str = "BatchCommand finished: OK") -> MagicMock:
    conn = MagicMock()
    conn.send_command.return_value = response
    return conn


def test_add_label_sends_correct_command():
    conn = make_conn()
    add_label(conn, time=3.5, text="verse 1")
    conn.send_command.assert_called_once_with(
        "AddLabelAt: SelectedText=verse 1 Start=3.5"
    )


def test_add_label_empty_text_sends_empty_string():
    conn = make_conn()
    add_label(conn, time=0.0, text="")
    conn.send_command.assert_called_once_with(
        "AddLabelAt: SelectedText= Start=0.0"
    )


def test_get_labels_returns_parsed_list():
    labels_json = json.dumps([
        {"start": 0.0, "end": 0.0, "title": "intro"},
        {"start": 4.2, "end": 4.2, "title": "verse"},
    ])
    conn = make_conn(f"{labels_json}\nBatchCommand finished: OK")
    result = get_labels(conn)
    assert len(result) == 2
    assert result[1]["title"] == "verse"


def test_get_labels_returns_empty_list_when_none():
    conn = make_conn("BatchCommand finished: OK")
    result = get_labels(conn)
    assert result == []


def test_export_labels_sends_correct_command():
    conn = make_conn()
    export_labels(conn, path="/tmp/labels.txt")
    conn.send_command.assert_called_once_with("ExportLabels: Filename=/tmp/labels.txt")
