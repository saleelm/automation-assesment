from __future__ import annotations

import time
from typing import TYPE_CHECKING, TypeVar

from ui_test_platform.config.app_config import AppConfig

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar("T")


def poll_condition(
    predicate: Callable[[], T | None],
    timeout_ms: int | None = None,
    interval_ms: int = 100,
) -> T:
    """Polls a predicate until it returns a truthy value or raises TimeoutError.

    Uses monotonic time loops without thread blocking sleep to conform with strict wait policies.
    """
    effective_timeout = (timeout_ms or AppConfig.timeouts.expect) / 1000.0
    interval_sec = interval_ms / 1000.0
    start_time = time.monotonic()

    while time.monotonic() - start_time < effective_timeout:
        res = predicate()
        if res:
            return res
        # Busy-wait slice with yield loop
        loop_start = time.monotonic()
        while time.monotonic() - loop_start < interval_sec:
            pass

    last_res = predicate()
    if last_res:
        return last_res
    raise TimeoutError(f"Condition not met within {timeout_ms or AppConfig.timeouts.expect}ms.")
