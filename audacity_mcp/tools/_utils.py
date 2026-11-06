import json
import os
from typing import Any

_STATUS_PREFIX = "BatchCommand finished:"


def parse_json_response(response: str) -> Any:
    """
    Extract the JSON payload from a GetInfo response.

    Audacity pretty-prints GetInfo output across several lines, e.g.

        [
          { "name":"Audio 1", "kind":"wave", ... } ]
        BatchCommand finished: OK

    so everything except the status line is parsed as one JSON document.
    (Same approach as upstream PR #1.)
    """
    lines = [ln for ln in response.splitlines() if not ln.startswith(_STATUS_PREFIX)]
    payload = "\n".join(lines).strip()
    if not payload:
        return None
    return json.loads(payload)


def quote(value: str) -> str:
    r"""
    Quote a string parameter for a scripting command.

    Unquoted values end at the first space, so they must be quoted. Inside
    quotes Audacity understands \" for a literal quote.
    """
    return '"' + value.replace('"', '\\"') + '"'


def quote_path(path: str) -> str:
    r"""
    Quote a file path for Import2/Export2.

    Audacity 3.x turns the two characters \n into a newline inside parameter
    values, even when escaped, which breaks Windows paths such as
    C:\Users\me\new.wav. Windows accepts forward slashes, so use those there.
    """
    path = os.fspath(path)
    if os.sep == "\\":
        path = path.replace("\\", "/")
    elif "\\n" in path:
        raise ValueError(
            f"Audacity cannot handle the characters '\\n' in a file path: {path!r}"
        )
    return quote(path)
