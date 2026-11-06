import pytest
from unittest.mock import MagicMock, call, patch
from audacity_mcp.tools.export import export_audio, export_selection, import_audio
from audacity_mcp.tools._utils import quote_path

OK = "BatchCommand finished: OK"


def make_conn() -> MagicMock:
    conn = MagicMock()
    conn.send_command.return_value = "BatchCommand finished: OK"
    return conn


TRACKS = '[ { "name":"Vocal", "kind":"wave" },\n  { "name":"Labels 1", "kind":"label" } ]\n' + OK


def make_project_conn() -> MagicMock:
    conn = MagicMock()
    conn.send_command.side_effect = lambda cmd: TRACKS if cmd == "GetInfo: Type=Tracks" else OK
    return conn


def test_export_audio_selects_whole_project_then_exports():
    """Export2 only exports the selection, so a full export must select everything.
    It uses Select (not the SelectAll menu command, which a label in edit mode swallows)
    with the exact track count (an out-of-range count opens a blocking dialog)."""
    conn = make_project_conn()
    export_audio(conn, path="/tmp/output.wav")
    assert conn.send_command.call_args_list == [
        call("GetInfo: Type=Tracks"),
        call("Select: Start=0 End=0 RelativeTo=Project Track=0 TrackCount=2 Mode=Set"),
        call('Export2: Filename="/tmp/output.wav" NumChannels=2'),
    ]


def test_export_audio_mono():
    conn = make_project_conn()
    export_audio(conn, path="/tmp/mono.wav", channels=1)
    conn.send_command.assert_called_with('Export2: Filename="/tmp/mono.wav" NumChannels=1')


def test_export_audio_quotes_paths_with_spaces():
    conn = make_project_conn()
    export_audio(conn, path="/tmp/my song/final mix.wav")
    conn.send_command.assert_called_with(
        'Export2: Filename="/tmp/my song/final mix.wav" NumChannels=2'
    )


def test_export_audio_refuses_empty_project():
    conn = make_conn()
    conn.send_command.return_value = "[ ]\n" + OK
    with pytest.raises(RuntimeError, match="no tracks"):
        export_audio(conn, path="/tmp/empty.wav")
    assert not any("Export2" in c.args[0] for c in conn.send_command.call_args_list)


def test_export_selection_uses_export2_without_selecting():
    """There is no ExportSel2 command; Export2 already exports the selection."""
    conn = make_conn()
    export_selection(conn, path="/tmp/clip.flac")
    conn.send_command.assert_called_once_with('Export2: Filename="/tmp/clip.flac" NumChannels=2')


def test_import_audio_quotes_path():
    conn = make_conn()
    import_audio(conn, path="/tmp/source take.mp3")
    conn.send_command.assert_called_once_with('Import2: Filename="/tmp/source take.mp3"')


def test_quote_path_escapes_double_quotes():
    assert quote_path('/tmp/say "hi".wav') == '"/tmp/say \\"hi\\".wav"'


def test_quote_path_uses_forward_slashes_on_windows():
    """Audacity turns the characters \\n into a newline, breaking C:\\...\\new.wav."""
    with patch("audacity_mcp.tools._utils.os.sep", "\\"):
        assert quote_path(r"C:\Users\me\new song.wav") == '"C:/Users/me/new song.wav"'


def test_quote_path_rejects_backslash_n_on_posix():
    with patch("audacity_mcp.tools._utils.os.sep", "/"):
        with pytest.raises(ValueError, match="cannot handle"):
            quote_path(r"/tmp/odd\name.wav")
