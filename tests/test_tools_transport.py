import pytest
from unittest.mock import MagicMock
from audacity_mcp.tools.transport import play, stop, rewind, undo


def make_conn() -> MagicMock:
    conn = MagicMock()
    conn.send_command.return_value = "BatchCommand finished: OK"
    return conn


def test_play_sends_play_command():
    conn = make_conn()
    play(conn)
    conn.send_command.assert_called_once_with("Play:")


def test_stop_sends_stop_command():
    conn = make_conn()
    stop(conn)
    conn.send_command.assert_called_once_with("Stop:")


def test_rewind_sends_cursor_to_start():
    conn = make_conn()
    rewind(conn)
    conn.send_command.assert_called_once_with("CursProjectStart:")


def test_undo_sends_undo_command():
    conn = make_conn()
    undo(conn)
    conn.send_command.assert_called_once_with("Undo:")
