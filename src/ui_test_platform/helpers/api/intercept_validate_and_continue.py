from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ui_test_platform.helpers.api.route_payload import parse_route_payload

if TYPE_CHECKING:
    from collections.abc import Callable

    from playwright.sync_api import Page, Route
    from pydantic import BaseModel

    from ui_test_platform.helpers.api.types import RouteCleanup, RouteMatcher


def intercept_validate_and_continue(
    page: Page,
    url_matcher: RouteMatcher,
    method: str | None = None,
    schema: type[BaseModel] | None = None,
    callback: Callable[[str, Any, str], None] | None = None,
) -> RouteCleanup:
    """Validates outgoing request payload, invokes callback, and continues route."""
    captured_errors: list[Exception] = []

    def handler(route: Route) -> None:
        try:
            req = route.request
            if method and req.method.upper() != method.upper():
                route.continue_()
                return

            payload = parse_route_payload(req)
            if schema and isinstance(payload, dict):
                schema.model_validate(payload)
            if callback:
                callback(req.method, payload, req.url)
            route.continue_()
        except Exception as e:
            captured_errors.append(e)
            route.continue_()

    page.route(url_matcher, handler)

    def cleanup() -> None:
        page.unroute(url_matcher, handler)
        if captured_errors:
            raise captured_errors[0]

    return cleanup
