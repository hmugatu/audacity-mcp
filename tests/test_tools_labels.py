import pytest
from unittest.mock import MagicMock, call
from audacity_mcp.tools.labels import add_label, get_labels, export_labels

OK = "BatchCommand finished: OK"

# Real Audacity 3.7.9 output: one [track_index, labels] entry per label track.
LABELS_RESPONSE = (
    '[ \n'
    '  [ 1,\n'
    '    [ \n'
    '      [ 1.5, 1.5, "verse 1" ],\n'
    '      [ 2, 3, "chorus" ] ] ] ]\n'
    + OK
)


def make_conn(response: str = OK) -> MagicMock:
    conn = MagicMock()
    conn.send_command.return_value = response
    return conn


def labels_reply(*labels, track=1):
    rows = ", ".join(f'[ {s}, {e}, "{t}" ]' for s, e, t in labels)
    return f"[ [ {track}, [ {rows} ] ] ]\n{OK}" if labels else f"[ ]\n{OK}"


def scripted_conn(replies: dict) -> MagicMock:
    """A conn whose GetInfo replies advance each time AddLabel is sent."""
    state = {"added": False}
    def send(cmd):
        if cmd == "AddLabel:":
            state["added"] = True
        if cmd == "GetInfo: Type=Labels":
            return replies["after" if state["added"] else "before"]
        return OK
    conn = MagicMock()
    conn.send_command.side_effect = send
    return conn


def test_add_label_into_empty_project():
    conn = scripted_conn({"before": labels_reply(), "after": labels_reply((3.5, 3.5, ""))})
    add_label(conn, time=3.5, text="verse 1")
    sent = [c.args[0] for c in conn.send_command.call_args_list]
    assert sent[0] == "SelectTime: Start=3.5 End=3.5 RelativeTo=ProjectStart"
    assert "AddLabel:" in sent
    assert sent[-1] == 'SetLabel: Label=0 Text="verse 1"'


def test_add_label_finds_index_of_label_inserted_between_others():
    conn = scripted_conn({
        "before": labels_reply((1, 1, "intro"), (9, 9, "outro")),
        "after":  labels_reply((1, 1, "intro"), (4, 6, ""), (9, 9, "outro")),
    })
    add_label(conn, time=4, end=6, text='the "drop"')
    sent = [c.args[0] for c in conn.send_command.call_args_list]
    assert sent[0] == "SelectTime: Start=4 End=6 RelativeTo=ProjectStart"
    assert sent[-1] == 'SetLabel: Label=1 Text="the \\"drop\\""'


def test_add_label_empty_text_skips_setlabel():
    conn = scripted_conn({"before": labels_reply(), "after": labels_reply((0, 0, ""))})
    add_label(conn, time=0.0, text="")
    assert not any(c.args[0].startswith("SetLabel") for c in conn.send_command.call_args_list)


def test_add_label_raises_if_nothing_was_added():
    conn = scripted_conn({"before": labels_reply(), "after": labels_reply()})
    with pytest.raises(RuntimeError, match="did not create a label"):
        add_label(conn, time=1.0, text="x")


def test_get_labels_returns_flat_dicts():
    result = get_labels(make_conn(LABELS_RESPONSE))
    assert result == [
        {"track": 1, "start": 1.5, "end": 1.5, "text": "verse 1"},
        {"track": 1, "start": 2, "end": 3, "text": "chorus"},
    ]


def test_get_labels_returns_empty_list_when_none():
    assert get_labels(make_conn("[ ]\n" + OK)) == []
    assert get_labels(make_conn(OK)) == []


def test_export_labels_writes_audacity_label_file(tmp_path):
    """ExportLabels opens a dialog that blocks the pipe, so write the file directly."""
    path = tmp_path / "labels.txt"
    conn = make_conn(LABELS_RESPONSE)
    assert export_labels(conn, path=str(path)) == 2
    conn.send_command.assert_called_once_with("GetInfo: Type=Labels")
    assert path.read_text() == "1.500000\t1.500000\tverse 1\n2.000000\t3.000000\tchorus\n"
