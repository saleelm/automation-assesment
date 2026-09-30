from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from playwright.sync_api import Page, Route

    from ui_test_platform.helpers.api.types import RouteCleanup, RouteMatcher


def intercept_passthrough_mutate(
    page: Page,
    url_matcher: RouteMatcher,
    mutator: Callable[[Any], Any],
) -> RouteCleanup:
    """Fetches real response, runs a mutation callback on the JSON body, and fulfills."""

    def handler(route: Route) -> None:
        response = route.fetch()
        try:
            body = response.json()
            mutated = mutator(body)
            route.fulfill(response=response, json=mutated)
            return
        except Exception:
            pass
        route.fulfill(response=response)

    page.route(url_matcher, handler)

    def cleanup() -> None:
        page.unroute(url_matcher, handler)

    return cleanup
