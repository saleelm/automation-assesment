from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from playwright.sync_api import Page, Route

    from ui_test_platform.helpers.api.types import RouteCleanup, RouteMatcher


def intercept_fulfill_json(
    page: Page,
    url_matcher: RouteMatcher,
    json_data: Any,
    status: int = 200,
) -> RouteCleanup:
    """Mocks network response with local JSON payload without hitting network."""

    def handler(route: Route) -> None:
        route.fulfill(status=status, json=json_data)

    page.route(url_matcher, handler)

    def cleanup() -> None:
        page.unroute(url_matcher, handler)

    return cleanup
