from __future__ import annotations

import json
from typing import TYPE_CHECKING
from urllib.parse import parse_qs

if TYPE_CHECKING:
    from playwright.sync_api import Request


def parse_route_payload(request: Request) -> object:
    """Parses outgoing route request payloads into JSON, Form dictionary, or string."""
    post_data = request.post_data
    if not post_data:
        return {}

    content_type = request.headers.get("content-type", "").lower()

    if "application/x-www-form-urlencoded" in content_type:
        parsed = parse_qs(post_data)
        return {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}

    stripped = post_data.strip()
    if "application/json" in content_type or stripped.startswith(("{", "[")):
        try:
            return json.loads(post_data)
        except Exception:
            return post_data

    return post_data
