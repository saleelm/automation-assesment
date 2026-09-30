from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import expect

from ui_test_platform.config.app_config import AppConfig
from ui_test_platform.enums.tags import Platform

if TYPE_CHECKING:
    from collections.abc import Callable
    from contextlib import AbstractContextManager

    from playwright.sync_api import Locator, Page, Response


class BasePage:
    """Base class for all Page Objects in the ui-test-platform framework."""

    def __init__(self, page: Page, platform: Platform = Platform.WEB) -> None:
        self.page = page
        self.platform = platform

    def goto(self, path: str = "/") -> None:
        """Navigates to relative or absolute path and handles cookie consent / gates."""
        target_url = path if path.startswith("http") else f"{AppConfig.base_url.rstrip('/')}/{path.lstrip('/')}"
        self.page.goto(target_url, wait_until="domcontentloaded")
        self.dismiss_cookie_banner()

    def dismiss_cookie_banner(self) -> None:
        """Dismisses cookie consent banners (e.g. Usercentrics CMP) if displayed."""
        try:
            # Common CMP selectors (Usercentrics shadow DOM / standard buttons)
            accept_button = self.page.locator(
                "button#uc-accept-all-button, "
                "button[data-testid='uc-accept-all-button'], "
                "#usercentrics-root button:has-text('Accept'), "
                "button:has-text('Accept All'), "
                "button:has-text('I Agree')"
            ).first
            if accept_button.is_visible(timeout=2000):
                accept_button.click()
        except Exception:
            # Non-blocking if consent banner does not appear
            pass

    def wait_for_url(
        self,
        url_or_predicate: str | Callable[[str], bool],
        timeout: int | None = None,
    ) -> None:
        self.page.wait_for_url(
            url_or_predicate,
            timeout=timeout or AppConfig.timeouts.expect,
        )

    def expect_title(self, text_or_regex: str, timeout: int | None = None) -> None:
        expect(self.page).to_have_title(
            text_or_regex,
            timeout=timeout or AppConfig.timeouts.expect,
        )

    def expect_url(self, text_or_regex: str, timeout: int | None = None) -> None:
        expect(self.page).to_have_url(
            text_or_regex,
            timeout=timeout or AppConfig.timeouts.expect,
        )

    def expect_visible(self, locator: Locator, timeout: int | None = None) -> None:
        expect(locator).to_be_visible(timeout=timeout or AppConfig.timeouts.expect)

    def reload(self) -> None:
        self.page.reload(wait_until="domcontentloaded")
        self.dismiss_cookie_banner()

    def wait_for_api_response(
        self,
        method: str,
        url_includes: str,
        query_params: dict[str, str] | None = None,
        status: int = 200,
        timeout: int | None = None,
    ) -> AbstractContextManager[Response]:
        """Expects an API response matching HTTP method, path fragment, and optional status code."""

        def predicate(response: Response) -> bool:
            if response.request.method.upper() != method.upper():
                return False
            parsed = urlparse(response.url)
            if url_includes not in parsed.path and url_includes not in response.url:
                return False
            if query_params:
                response_params = parse_qs(parsed.query)
                for key, val in query_params.items():
                    if val not in response_params.get(key, []):
                        return False
            return response.status == status

        return self.page.expect_response(
            predicate,
            timeout=timeout or AppConfig.timeouts.api_route_fetch,
        )
