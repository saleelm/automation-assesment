from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ui_test_platform.config.app_config import AppConfig
from ui_test_platform.enums.tags import Platform
from ui_test_platform.pages.base_page import BasePage

if TYPE_CHECKING:
    from playwright.sync_api import Locator, Page

logger = logging.getLogger("ui_test_platform.pages.home")


class HomePage(BasePage):
    """Page Object for Stumble Guys Portal Home Page."""

    def __init__(self, page: Page, platform: Platform = Platform.WEB) -> None:
        super().__init__(page, platform)

    @property
    def logo(self) -> Locator:
        return self.page.locator("img[alt='stumble guys logo']").first

    @property
    def play_nav_link(self) -> Locator:
        return self.page.locator("nav a[href='/play']").first

    @property
    def shop_nav_link(self) -> Locator:
        return self.page.locator("nav a[href='/shop']").first

    @property
    def hero_play_now_button(self) -> Locator:
        return self.page.locator("button:has-text('Play Now!'), a[href='/play'] button").first

    @property
    def avatar_menu_trigger(self) -> Locator:
        return self.page.locator("button:has(img[alt='avatar']):visible").first

    @property
    def login_button(self) -> Locator:
        return self.page.locator("button:has-text('Login'):visible, [class*='AuthButton_login']:visible").first

    def navigate(self) -> HomePage:
        """Navigates to Home Page and waits for logo and main navigation anchors."""
        logger.info("Navigating to Home Page and verifying logo")
        self.goto("/")
        self.expect_visible(self.logo, timeout=AppConfig.timeouts.navigate_expect)
        return self

    def open_login_modal(self) -> None:
        """Triggers the login modal from the header avatar dropdown."""
        logger.info("Opening login modal from header avatar dropdown")
        trigger = self.avatar_menu_trigger
        self.expect_visible(trigger)
        trigger.click()
        login_btn = self.login_button
        self.expect_visible(login_btn)
        login_btn.click()
