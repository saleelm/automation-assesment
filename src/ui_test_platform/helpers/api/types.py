from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

RouteMatcher = str | re.Pattern[str] | Callable[[str], bool]
JsonValue = dict[str, Any] | list[Any] | str | int | float | bool | None
RouteCleanup = Callable[[], None]
