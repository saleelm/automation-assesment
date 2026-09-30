from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from playwright.sync_api import Page, Route

    from ui_test_platform.helpers.api.types import RouteCleanup, RouteMatcher


def intercept_modify_response(
    page: Page,
    url_matcher: RouteMatcher,
    overrides: dict[str, Any],
) -> RouteCleanup:
    """Fetches real response, modifies top-level fields with overrides, and fulfills."""

    def handler(route: Route) -> None:
        response = route.fetch()
        try:
            body = response.json()
            if isinstance(body, dict):
                body.update(overrides)
                route.fulfill(response=response, json=body)
                return
        except Exception:
            pass
        route.fulfill(response=response)

    page.route(url_matcher, handler)

    def cleanup() -> None:
        page.unroute(url_matcher, handler)

    return cleanup
