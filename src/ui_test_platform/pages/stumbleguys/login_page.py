from __future__ import annotations

from typing import TYPE_CHECKING

from ui_test_platform.config.app_config import AppConfig
from ui_test_platform.constants.login_locators import LoginLocators
from ui_test_platform.enums.tags import Platform
from ui_test_platform.pages.base_page import BasePage

if TYPE_CHECKING:
    from playwright.sync_api import Locator, Page


class LoginPage(BasePage):
    """Page Object for Stumble Guys authentication flow."""

    def __init__(self, page: Page, platform: Platform = Platform.WEB) -> None:
        super().__init__(page, platform)
        self.locators = LoginLocators()

    @property
    def avatar_trigger(self) -> Locator:
        return self.page.locator("button:has(img[alt='avatar']):visible").first

    @property
    def nav_login_button(self) -> Locator:
        return self.page.locator("button:has-text('Login'):visible, [class*='AuthButton_login']:visible").first

    @property
    def auth_modal(self) -> Locator:
        return self.page.locator(
            "[role='dialog'], .modal, div[class*='Modal'], div[class*='login'], div[class*='Dropdown']"
        ).first

    @property
    def email_input(self) -> Locator:
        return self.page.locator(
            "input[type='email'], input[name='email'], input[placeholder*='email' i], #username, #email"
        ).first

    @property
    def password_input(self) -> Locator:
        return self.page.locator("input[type='password'], input[name='password'], #password").first

    @property
    def submit_button(self) -> Locator:
        return self.page.locator(
            "form button[type='submit']:visible, [role='dialog'] button[type='submit']:visible, "
            "#kc-login:visible, button:has-text('Continue'):visible, button:has-text('Sign In'):visible"
        ).first

    @property
    def error_message(self) -> Locator:
        return self.page.locator(
            "#input-error:visible, .alert-error:visible, .text-red-500:visible, "
            "[role='alert']:visible, [data-testid='error-message']:visible"
        ).first

    def navigate(self) -> LoginPage:
        """Navigates to home page and triggers the login flow."""
        self.goto("/")
        self.open_login()
        return self

    def open_login(self) -> None:
        """Opens login dropdown or dialog."""
        # Ensure header avatar is visible and clicked
        trigger = self.avatar_trigger
        self.expect_visible(trigger, timeout=AppConfig.timeouts.navigate_expect)
        trigger.click()
        btn = self.nav_login_button
        self.expect_visible(btn, timeout=AppConfig.timeouts.action)

    def login(self, email: str, password: str) -> None:
        """Fills login credentials and submits."""
        # Click login button to open auth dialog/redirect
        self.nav_login_button.click()

        if self.email_input.is_visible(timeout=3000):
            self.email_input.fill(email)
            if self.submit_button.is_visible(timeout=2000):
                self.submit_button.click()

            if self.password_input.is_visible(timeout=3000):
                self.password_input.fill(password)
                if self.submit_button.is_visible(timeout=2000):
                    self.submit_button.click()

    def submit_invalid_credentials(self, email: str) -> None:
        """Submits invalid email/username to trigger form validation."""
        self.nav_login_button.click()
        if self.email_input.is_visible(timeout=3000):
            self.email_input.fill(email)
            if self.submit_button.is_visible(timeout=2000):
                self.submit_button.click()
