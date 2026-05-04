import json
import pytest
from unittest.mock import MagicMock
from audacity_mcp.tools.tracks import (
    get_tracks, get_selection, select_time, select_tracks,
)


def make_conn(response: str) -> MagicMock:
    conn = MagicMock()
    conn.send_command.return_value = response
    return conn


def test_get_tracks_returns_parsed_list():
    tracks_json = json.dumps([
        {"name": "Vocal", "kind": "wave", "start": 0.0, "end": 5.2},
        {"name": "Guitar", "kind": "wave", "start": 0.0, "end": 5.2},
    ])
    conn = make_conn(f"{tracks_json}\nBatchCommand finished: OK")
    result = get_tracks(conn)
    assert len(result) == 2
    assert result[0]["name"] == "Vocal"


def test_get_tracks_returns_empty_list_when_no_tracks():
    conn = make_conn("BatchCommand finished: OK")
    result = get_tracks(conn)
    assert result == []


def test_get_selection_returns_start_and_end():
    sel_json = json.dumps({"start": 1.0, "end": 4.5, "tracks": "all"})
    conn = make_conn(f"{sel_json}\nBatchCommand finished: OK")
    result = get_selection(conn)
    assert result["start"] == 1.0
    assert result["end"] == 4.5


def test_select_time_sends_correct_command():
    conn = make_conn("BatchCommand finished: OK")
    select_time(conn, start=1.5, end=10.0)
    conn.send_command.assert_called_once_with(
        "SelectTime: Start=1.5 End=10.0 RelativeTo=ProjectStart"
    )


def test_select_tracks_sends_correct_command():
    conn = make_conn("BatchCommand finished: OK")
    select_tracks(conn, track_index=2)
    conn.send_command.assert_called_once_with(
        "SelectTracks: Track=2 TrackCount=1 Mode=Set"
    )
