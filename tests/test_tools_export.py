import pytest
from unittest.mock import MagicMock
from audacity_mcp.tools.export import export_audio, export_selection, import_audio


def make_conn() -> MagicMock:
    conn = MagicMock()
    conn.send_command.return_value = "BatchCommand finished: OK"
    return conn


def test_export_audio_sends_correct_command():
    conn = make_conn()
    export_audio(conn, path="/tmp/output.wav")
    conn.send_command.assert_called_once_with(
        "Export2: Filename=/tmp/output.wav Numchannels=2"
    )


def test_export_audio_mono():
    conn = make_conn()
    export_audio(conn, path="/tmp/mono.wav", channels=1)
    conn.send_command.assert_called_once_with(
        "Export2: Filename=/tmp/mono.wav Numchannels=1"
    )


def test_export_selection_sends_correct_command():
    conn = make_conn()
    export_selection(conn, path="/tmp/clip.flac")
    conn.send_command.assert_called_once_with(
        "ExportSel2: Filename=/tmp/clip.flac Numchannels=2"
    )


def test_import_audio_sends_correct_command():
    conn = make_conn()
    import_audio(conn, path="/tmp/source.mp3")
    conn.send_command.assert_called_once_with("Import2: Filename=/tmp/source.mp3")
