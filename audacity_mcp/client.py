"""
client.py — Audacity named-pipe connection.

Audacity must be running with mod-script-pipe enabled:
  Edit → Preferences → Modules → mod-script-pipe → Enabled → restart Audacity

macOS/Linux pipes appear in /tmp/ as:
  audacity_script_pipe.to.{PID}
  audacity_script_pipe.from.{PID}

Windows pipes are at fixed paths:
  \\\\.\\pipe\\ToSrvPipe
  \\\\.\\pipe\\FromSrvPipe
"""

import glob
import logging
import platform

logger = logging.getLogger(__name__)


class AudacityConnection:
    """Send scripting commands to Audacity via mod-script-pipe."""

    def __init__(self):
        self._to_pipe   = None
        self._from_pipe = None
        self._connected = False

    def _find_pipes(self):
        """Return (to_pipe_path, from_pipe_path) for the current OS."""
        if platform.system() == "Windows":
            return r"\\.\pipe\ToSrvPipe", r"\\.\pipe\FromSrvPipe"

        candidates = sorted(glob.glob("/tmp/audacity_script_pipe.to.*"))
        if not candidates:
            raise ConnectionError(
                "Audacity pipe not found. "
                "Enable mod-script-pipe in Audacity Preferences → Modules, "
                "then restart Audacity."
            )
        to_pipe   = candidates[-1]
        from_pipe = to_pipe.replace(".to.", ".from.")
        return to_pipe, from_pipe

    def connect(self) -> bool:
        """Open both pipes. Returns True on success."""
        if self._connected:
            return True
        try:
            to_path, from_path = self._find_pipes()
        except ConnectionError:
            raise  # let caller see the "mod-script-pipe not enabled" message
        try:
            self._to_pipe   = open(to_path,   "w", encoding="utf-8")
            self._from_pipe = open(from_path,  "r", encoding="utf-8")
            self._connected = True
            logger.info("Connected to Audacity pipes.")
            return True
        except OSError as exc:
            logger.error("Could not open Audacity pipes: %s", exc)
            raise ConnectionError(f"Could not open Audacity pipes: {exc}") from exc

    def disconnect(self):
        """Close pipes cleanly."""
        if self._to_pipe:
            self._to_pipe.close()
            self._to_pipe = None
        if self._from_pipe:
            self._from_pipe.close()
            self._from_pipe = None
        self._connected = False

    def send_command(self, command: str) -> str:
        """
        Send a scripting command to Audacity and return the full response string.

        Raises RuntimeError if Audacity reports failure.
        """
        if not self._connected:
            raise RuntimeError("Not connected. Call connect() first.")

        logger.debug("→ %s", command)
        self._to_pipe.write(command + "\n")
        self._to_pipe.flush()

        response = self._read_response()
        logger.debug("← %s", response[:120])

        if "BatchCommand finished: Failed" in response:
            raise RuntimeError(f"Audacity command failed: {command!r}\nResponse: {response}")

        return response.strip()

    def _read_response(self) -> str:
        """Read characters from the from-pipe until the double-newline sentinel."""
        buf = ""
        while not buf.endswith("\n\n"):
            ch = self._from_pipe.read(1)
            if not ch:
                raise RuntimeError("Audacity pipe closed before response was complete.")
            buf += ch
        return buf
