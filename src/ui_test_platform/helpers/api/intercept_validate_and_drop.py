from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ui_test_platform.helpers.api.route_payload import parse_route_payload

if TYPE_CHECKING:
    from collections.abc import Callable

    from playwright.sync_api import Page, Route
    from pydantic import BaseModel

    from ui_test_platform.helpers.api.types import RouteCleanup, RouteMatcher


def intercept_validate_and_drop(
    page: Page,
    url_matcher: RouteMatcher,
    schema: type[BaseModel] | None = None,
    callback: Callable[[Any], None] | None = None,
) -> RouteCleanup:
    """Intercepts matching requests, validates with pydantic, executes callback, and drops/aborts the request."""
    captured_errors: list[Exception] = []

    def handler(route: Route) -> None:
        try:
            payload = parse_route_payload(route.request)
            if schema and isinstance(payload, dict):
                schema.model_validate(payload)
            if callback:
                callback(payload)
            route.abort("failed")
        except Exception as e:
            captured_errors.append(e)
            route.abort("failed")

    page.route(url_matcher, handler)

    def cleanup() -> None:
        page.unroute(url_matcher, handler)
        if captured_errors:
            raise captured_errors[0]

    return cleanup
