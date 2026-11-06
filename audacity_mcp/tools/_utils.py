import json
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
