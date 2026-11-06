import json
import os
import platform
import threading
import pytest
from unittest.mock import patch, MagicMock
from audacity_mcp.client import AudacityConnection


def test_find_pipes_posix_uses_uid_named_pipes():
    with patch("audacity_mcp.client.platform.system", return_value="Darwin"), \
         patch("audacity_mcp.client.os.getuid", return_value=501, create=True), \
         patch("audacity_mcp.client.os.path.exists", return_value=True):
        t, f = AudacityConnection()._find_pipes()
    assert t == "/tmp/audacity_script_pipe.to.501"
    assert f == "/tmp/audacity_script_pipe.from.501"


def test_find_pipes_raises_when_audacity_not_running():
    with patch("audacity_mcp.client.platform.system", return_value="Darwin"), \
         patch("audacity_mcp.client.os.getuid", return_value=501, create=True), \
         patch("audacity_mcp.client.os.path.exists", return_value=False):
        conn = AudacityConnection()
        with pytest.raises(ConnectionError, match="mod-script-pipe"):
            conn._find_pipes()


def test_find_pipes_windows_returns_named_pipes():
    with patch("audacity_mcp.client.platform.system", return_value="Windows"):
        conn = AudacityConnection()
        t, f = conn._find_pipes()
    assert t == r"\\.\pipe\ToSrvPipe"
    assert f == r"\\.\pipe\FromSrvPipe"


def test_send_command_writes_command_and_returns_response():
    conn = AudacityConnection()
    response_data = 'BatchCommand finished: OK\n\n'

    mock_to   = MagicMock()
    mock_from = MagicMock()
    mock_from.read.side_effect = list(response_data)

    conn._to_pipe   = mock_to
    conn._from_pipe = mock_from
    conn._connected = True

    result = conn.send_command("Normalize: PeakLevel=-1.0")

    mock_to.write.assert_called_once_with("Normalize: PeakLevel=-1.0\n")
    mock_to.flush.assert_called_once()
    assert result == "BatchCommand finished: OK"


def test_send_command_returns_json_payload():
    conn = AudacityConnection()
    payload       = '[{"name":"Audio Track","kind":"wave"}]'
    response_data = payload + '\nBatchCommand finished: OK\n\n'

    mock_to   = MagicMock()
    mock_from = MagicMock()
    mock_from.read.side_effect = list(response_data)

    conn._to_pipe   = mock_to
    conn._from_pipe = mock_from
    conn._connected = True

    result = conn.send_command("GetInfo: Type=Tracks")
    assert payload in result


def test_send_command_raises_on_error_response():
    conn = AudacityConnection()
    response_data = 'BatchCommand finished: Failed!\n\n'

    mock_to   = MagicMock()
    mock_from = MagicMock()
    mock_from.read.side_effect = list(response_data)

    conn._to_pipe   = mock_to
    conn._from_pipe = mock_from
    conn._connected = True

    with pytest.raises(RuntimeError, match="Failed"):
        conn.send_command("BadCommand:")


def test_send_command_decodes_multibyte_utf8_split_across_reads():
    """Bytes are buffered and decoded once, so a split character survives."""
    conn = AudacityConnection()
    data = '[{"name":"Café"}]\nBatchCommand finished: OK\n\n'.encode("utf-8")
    split = data.index("é".encode()) + 1  # cut through the 2-byte é
    chunks = [data[:split], data[split:]]

    conn._to_pipe   = MagicMock()
    conn._from_fd   = 99
    conn._connected = True
    with patch("audacity_mcp.client.select.select", return_value=([99], [], [])), \
         patch("audacity_mcp.client.os.read", side_effect=chunks):
        result = conn.send_command("GetInfo: Type=Tracks")
    assert "Café" in result


posix_only = pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="needs POSIX FIFOs")


def _fake_pipes(tmp_path):
    to_path   = str(tmp_path / "to")
    from_path = str(tmp_path / "from")
    os.mkfifo(to_path)
    os.mkfifo(from_path)
    return to_path, from_path


@posix_only
def test_connect_fails_fast_on_stale_pipe(tmp_path):
    """Pipes left behind by a closed Audacity must not hang connect()."""
    pipes = _fake_pipes(tmp_path)
    conn = AudacityConnection()
    with patch.object(conn, "_find_pipes", return_value=pipes):
        with pytest.raises(ConnectionError, match="^Found .* not listening"):
            conn.connect()
    assert not conn._connected


@posix_only
def test_round_trip_over_real_fifos(tmp_path):
    to_path, from_path = _fake_pipes(tmp_path)
    received = []

    def fake_audacity():
        with open(to_path, "r") as cmd_in, open(from_path, "w") as reply_out:
            received.append(cmd_in.readline())
            reply_out.write('[\n  {"name":"Audio 1"} ]\nBatchCommand finished: OK\n\n')

    # The server must be reading before connect() opens the to-pipe.
    server = threading.Thread(target=fake_audacity, daemon=True)
    to_reader = os.open(to_path, os.O_RDONLY | os.O_NONBLOCK)  # keeps open() from failing
    server.start()
    conn = AudacityConnection(timeout=5)
    with patch.object(conn, "_find_pipes", return_value=(to_path, from_path)):
        conn.connect()
    result = conn.send_command("GetInfo: Type=Tracks")
    server.join(5)
    os.close(to_reader)
    conn.disconnect()

    assert received == ["GetInfo: Type=Tracks\n"]
    assert '"Audio 1"' in result


@posix_only
def test_timeout_disconnects_so_next_call_reconnects(tmp_path):
    to_path, from_path = _fake_pipes(tmp_path)
    to_reader = os.open(to_path, os.O_RDONLY | os.O_NONBLOCK)  # silent "Audacity"
    conn = AudacityConnection(timeout=0.2)
    with patch.object(conn, "_find_pipes", return_value=(to_path, from_path)):
        conn.connect()
    with pytest.raises(RuntimeError, match="no reply"):
        conn.send_command("Help:")
    os.close(to_reader)
    assert not conn._connected
