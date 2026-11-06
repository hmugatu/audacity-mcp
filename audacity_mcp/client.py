"""
client.py — Audacity named-pipe connection.

Audacity 3.x must be running with mod-script-pipe enabled:
  Edit → Preferences → Modules → mod-script-pipe → Enabled → restart Audacity
(Audacity 4.0 does not ship the scripting pipe.)

macOS/Linux pipes are named after the *user id* (see Audacity's
modules/scripting/mod-script-pipe/PipeServer.cpp):
  /tmp/audacity_script_pipe.to.{UID}
  /tmp/audacity_script_pipe.from.{UID}

Windows pipes are at fixed paths:
  \\\\.\\pipe\\ToSrvPipe
  \\\\.\\pipe\\FromSrvPipe
"""

import errno
import logging
import os
import platform
import select
import time

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 60.0  # seconds to wait for a reply; long effects need headroom

_NOT_RUNNING = (
    "Make sure Audacity 3.x is running and mod-script-pipe is enabled "
    "(Preferences → Modules → mod-script-pipe → Enabled, then restart Audacity)."
)


class AudacityConnection:
    """Send scripting commands to Audacity via mod-script-pipe."""

    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        self.timeout    = timeout
        self._to_pipe   = None
        self._from_pipe = None   # Windows: text file object
        self._from_fd   = None   # POSIX: raw fd, read with select() + timeout
        self._connected = False

    def _find_pipes(self):
        """Return (to_pipe_path, from_pipe_path) for the current OS."""
        if platform.system() == "Windows":
            return r"\\.\pipe\ToSrvPipe", r"\\.\pipe\FromSrvPipe"

        uid = os.getuid()
        to_pipe   = f"/tmp/audacity_script_pipe.to.{uid}"
        from_pipe = f"/tmp/audacity_script_pipe.from.{uid}"
        if not (os.path.exists(to_pipe) and os.path.exists(from_pipe)):
            raise ConnectionError(f"Audacity pipe not found ({to_pipe}). {_NOT_RUNNING}")
        return to_pipe, from_pipe

    def connect(self) -> bool:
        """Open both pipes. Returns True on success."""
        if self._connected:
            return True
        to_path, from_path = self._find_pipes()
        try:
            if platform.system() == "Windows":
                self._to_pipe   = open(to_path,   "w", encoding="utf-8")
                self._from_pipe = open(from_path, "r", encoding="utf-8")
            else:
                self._open_posix(to_path, from_path)
        except ConnectionError:  # already has a clear message; must precede OSError
            self.disconnect()
            raise
        except OSError as exc:
            self.disconnect()
            logger.error("Could not open Audacity pipes: %s", exc)
            raise ConnectionError(f"Could not open Audacity pipes: {exc}") from exc
        self._connected = True
        logger.info("Connected to Audacity pipes.")
        return True

    def _open_posix(self, to_path: str, from_path: str) -> None:
        # A blocking open() of a FIFO that nobody is reading waits forever,
        # which is exactly what happens with pipes left behind by a crashed
        # or closed Audacity. O_NONBLOCK makes that case fail fast (ENXIO).
        try:
            to_fd = os.open(to_path, os.O_WRONLY | os.O_NONBLOCK)
        except OSError as exc:
            if exc.errno == errno.ENXIO:
                raise ConnectionError(
                    f"Found {to_path} but Audacity is not listening on it "
                    f"(stale pipe from a previous session?). {_NOT_RUNNING}"
                ) from exc
            raise
        os.set_blocking(to_fd, True)
        self._to_pipe = os.fdopen(to_fd, "w", encoding="utf-8")
        self._from_fd = os.open(from_path, os.O_RDONLY | os.O_NONBLOCK)

    def disconnect(self):
        """Close pipes cleanly."""
        for f in (self._to_pipe, self._from_pipe):
            if f:
                try:
                    f.close()
                except OSError:
                    pass
        if self._from_fd is not None:
            try:
                os.close(self._from_fd)
            except OSError:
                pass
        self._to_pipe = self._from_pipe = self._from_fd = None
        self._connected = False

    def send_command(self, command: str) -> str:
        """
        Send a scripting command to Audacity and return the full response string.

        Raises RuntimeError if Audacity reports failure. If the pipe breaks or
        no reply arrives within ``timeout`` seconds, the connection is dropped
        (so the next call reconnects) and RuntimeError is raised.
        """
        if not self._connected:
            raise RuntimeError("Not connected. Call connect() first.")

        logger.debug("→ %s", command)
        try:
            self._to_pipe.write(command + "\n")
            self._to_pipe.flush()
            response = self._read_response()
        except (OSError, TimeoutError) as exc:
            self.disconnect()
            raise RuntimeError(
                f"Lost connection to Audacity while running {command!r}: {exc}"
            ) from exc
        logger.debug("← %s", response[:120])

        if "BatchCommand finished: Failed" in response:
            raise RuntimeError(f"Audacity command failed: {command!r}\nResponse: {response}")

        return response.strip()

    def _read_response(self) -> str:
        """Read from the from-pipe until the double-newline sentinel."""
        if self._from_fd is None:
            return self._read_response_file()

        buf = b""
        deadline = time.monotonic() + self.timeout
        while not buf.endswith(b"\n\n"):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"no reply from Audacity within {self.timeout:g}s")
            ready, _, _ = select.select([self._from_fd], [], [], remaining)
            if not ready:
                continue
            chunk = os.read(self._from_fd, 65536)
            if not chunk:
                # EOF: Audacity hasn't (re)attached its writer yet. Back off
                # briefly instead of spinning; the deadline still applies.
                time.sleep(0.01)
                continue
            buf += chunk
        # Decode once at the end so multi-byte UTF-8 split across reads is safe.
        return buf.decode("utf-8", errors="replace")

    def _read_response_file(self) -> str:
        """Windows path: read characters until the double-newline sentinel."""
        buf = ""
        while not buf.endswith("\n\n"):
            ch = self._from_pipe.read(1)
            if not ch:
                raise RuntimeError("Audacity pipe closed before response was complete.")
            buf += ch
        return buf
