from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import BrowserContext, Page


def seed_interstitial_skip_storage(context: BrowserContext) -> None:
    """Seeds flags into localStorage/sessionStorage to bypass onboarding or cookie consent."""
    context.add_init_script(
        """
        try {
            window.localStorage.setItem('cookie_consent', 'accepted');
            window.localStorage.setItem('usercentrics_consent', 'true');
            window.sessionStorage.setItem('onboarding_completed', 'true');
        } catch (e) {}
        """
    )


def apply_interstitial_skip(page: Page) -> None:
    """Evaluates script on active page to bypass interstitial gates if present."""
    page.evaluate(
        """
        try {
            window.localStorage.setItem('cookie_consent', 'accepted');
            window.sessionStorage.setItem('onboarding_completed', 'true');
        } catch (e) {}
        """
    )
