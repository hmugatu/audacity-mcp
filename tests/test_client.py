import json
import platform
import pytest
from unittest.mock import patch, MagicMock
from audacity_mcp.client import AudacityConnection


def test_find_pipes_macos_returns_matching_files(tmp_path):
    to_pipe   = tmp_path / "audacity_script_pipe.to.12345"
    from_pipe = tmp_path / "audacity_script_pipe.from.12345"
    to_pipe.touch()
    from_pipe.touch()

    with patch("audacity_mcp.client.glob.glob", return_value=[str(to_pipe)]):
        with patch("audacity_mcp.client.platform.system", return_value="Darwin"):
            conn = AudacityConnection()
            t, f = conn._find_pipes()
    assert t == str(to_pipe)
    assert f == str(from_pipe)


def test_find_pipes_raises_when_audacity_not_running():
    with patch("audacity_mcp.client.glob.glob", return_value=[]):
        with patch("audacity_mcp.client.platform.system", return_value="Darwin"):
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
