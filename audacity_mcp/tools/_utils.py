import json
from typing import Any


def parse_json_response(response: str) -> Any:
    """Extract the JSON payload from a GetInfo response (first line)."""
    first_line = response.split("\n")[0].strip()
    if not first_line or first_line.startswith("BatchCommand"):
        return None
    return json.loads(first_line)
