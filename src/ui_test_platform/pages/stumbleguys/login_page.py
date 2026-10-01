from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ui_test_platform.config.app_config import AppConfig
from ui_test_platform.constants.login_locators import LoginLocators
from ui_test_platform.enums.tags import Platform
from ui_test_platform.pages.base_page import BasePage

if TYPE_CHECKING:
    from playwright.sync_api import Locator, Page

logger = logging.getLogger("ui_test_platform.pages.login")


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

    @property
    def otp_inputs(self) -> Locator:
        return self.page.locator(
            "input[autocomplete='one-time-code']:visible, "
            "input[aria-label*='digit' i]:visible, "
            "input[placeholder*='code' i]:visible, "
            "input[maxlength='6']:visible, "
            "input[type='tel']:visible"
        )

    def enter_otp(self, code: str) -> None:
        """Enters 6-digit OTP code into either a single field or 6 discrete digit inputs."""
        logger.info("Entering 6-digit OTP verification code: %s", code)
        inputs = self.otp_inputs
        count = inputs.count()

        if count >= 6:
            # 6 separate digit inputs
            for i in range(min(6, len(code))):
                inputs.nth(i).fill(code[i])
        elif count >= 1:
            # Single consolidated OTP field
            inputs.first.fill(code)

        if self.submit_button.is_visible(timeout=2000):
            logger.info("Clicking submit button for OTP verification")
            self.submit_button.click()

    def navigate(self) -> LoginPage:
        """Navigates to home page and triggers the login flow."""
        self.goto("/")
        self.open_login()
        return self

    def open_login(self) -> None:
        """Opens login dropdown or dialog."""
        logger.info("Opening login menu via avatar trigger")
        # Ensure header avatar is visible and clicked
        trigger = self.avatar_trigger
        self.expect_visible(trigger, timeout=AppConfig.timeouts.navigate_expect)
        trigger.click()
        btn = self.nav_login_button
        self.expect_visible(btn, timeout=AppConfig.timeouts.action)

    def login(self, email: str, password: str) -> None:
        """Fills login credentials and submits."""
        logger.info("Executing login flow for email: %s", email)
        # Click login button to open auth dialog/redirect
        self.nav_login_button.click()

        if self.email_input.is_visible(timeout=3000):
            logger.info("Entering email into login dialog")
            self.email_input.fill(email)
            if self.submit_button.is_visible(timeout=2000):
                self.submit_button.click()

            if self.password_input.is_visible(timeout=3000):
                logger.info("Entering password into login dialog")
                self.password_input.fill(password)
                if self.submit_button.is_visible(timeout=2000):
                    self.submit_button.click()

    def submit_invalid_credentials(self, email: str) -> None:
        """Submits invalid email/username to trigger form validation."""
        logger.info("Submitting invalid credentials: '%s'", email)
        self.nav_login_button.click()
        if self.email_input.is_visible(timeout=3000):
            self.email_input.fill(email)
            if self.submit_button.is_visible(timeout=2000):
                self.submit_button.click()

    def initiate_signup_or_login(self, email: str) -> None:
        """Initiates the unified Scopely ID sign up / login pipeline for a given email."""
        logger.info("Initiating sign up / login pipeline for: %s", email)
        self.goto("/")
        self.open_login()
        self.nav_login_button.click()

        # Click Continue with email
        continue_email_btn = self.page.locator("button:has-text('Continue with email'):visible").first
        self.expect_visible(continue_email_btn, timeout=AppConfig.timeouts.action)
        continue_email_btn.click()

        # Wait for redirect to Scopely ID authorization portal
        scopely_email_input = self.page.locator("input[name='email'], input[placeholder*='email' i]").first
        self.expect_visible(scopely_email_input, timeout=AppConfig.timeouts.navigate_expect)
        logger.info("Entering email '%s' on Scopely ID portal", email)
        scopely_email_input.fill(email)

        scopely_continue_btn = self.page.locator("button:has-text('Continue'):visible").first
        self.expect_visible(scopely_continue_btn, timeout=AppConfig.timeouts.action)
        scopely_continue_btn.click()

    def submit_scopely_signup_agreement(self) -> None:
        """Agrees to terms on Scopely ID portal to trigger verification email dispatch."""
        logger.info("Confirming Scopely account creation agreement")
        agree_btn = self.page.locator("button:has-text('Agree and get sign up link')").first
        self.expect_visible(agree_btn, timeout=AppConfig.timeouts.navigate_expect)
        agree_btn.click()

        # Assert confirmation screen is displayed
        confirmation = self.page.get_by_text("Check your inbox!").first
        self.expect_visible(confirmation, timeout=AppConfig.timeouts.navigate_expect)
        logger.info("Scopely ID confirmed verification email dispatch successfully")
