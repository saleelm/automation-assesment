from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from urllib.parse import urlparse

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
            "input[inputmode='numeric']:visible, "
            "input[aria-label*='digit' i]:visible, "
            "input[placeholder*='code' i]:visible, "
            "input[maxlength='6']:visible, "
            "input[maxlength='1']:visible, "
            "input[type='tel']:visible"
        )

    def enter_otp(self, code: str) -> None:
        """Enters 6-digit OTP code into either a single field or 6 discrete digit inputs."""
        logger.info("Entering 6-digit OTP verification code: %s", code)

        # Wait for OTP input field to appear
        first_input = self.page.locator(
            "input[autocomplete='one-time-code'], "
            "input[inputmode='numeric'], "
            "input[aria-label*='digit' i], "
            "input[placeholder*='code' i], "
            "input[maxlength='6'], "
            "input[maxlength='1'], "
            "input[type='tel']"
        ).first
        self.expect_visible(first_input, timeout=AppConfig.timeouts.navigate_expect)

        inputs = self.otp_inputs
        count = inputs.count()
        logger.info("Found %d OTP input element(s)", count)

        if count >= 6:
            # Click the first OTP box, then type all digits via the global keyboard.
            # This mirrors real user behaviour: focus box 1, then press keys naturally.
            # Scopely's widget auto-advances focus with each keydown event — using
            # per-input press_sequentially breaks this because we re-click each box
            # ourselves, potentially resetting the widget state.
            inputs.first.click()
            self.page.keyboard.type(code, delay=100)
        elif count >= 1:
            # Single consolidated OTP field
            inputs.first.click()
            self.page.keyboard.type(code, delay=50)

        # If a verify / submit button is still visible (no auto-submit), click it.
        # We do NOT wrap in expect_navigation here because the form may have already
        # triggered a navigation from the last digit fill — wrapping causes a timeout.
        verify_btn = self.page.locator(
            "button:has-text('Verify'):visible, button:has-text('Submit'):visible, "
            "button:has-text('Sign In'):visible, button:has-text('Log In'):visible, "
            "button:has-text('Continue'):visible, form button[type='submit']:visible"
        ).first
        try:
            if verify_btn.is_visible(timeout=3000) and verify_btn.is_enabled(timeout=2000):
                logger.info("Clicking submit/verify button for OTP verification")
                verify_btn.click()
        except Exception as e:
            logger.info("Verify button not present or already auto-submitted: %s", e)

        # After OTP submission (auto or manual), wait for the redirect back to the app.
        # IMPORTANT: check the *hostname* — not a substring — because the Scopely authorize
        # URL itself contains "stumbleguys.com" as the redirect_uri query parameter, which
        # would cause a naive substring check to match immediately while still on Scopely.
        try:
            logger.info("Waiting for post-OTP redirect back to app domain...")
            self.page.wait_for_url(
                lambda url: urlparse(url).hostname in ("www.stumbleguys.com", "stumbleguys.com"),
                wait_until="domcontentloaded",
                timeout=AppConfig.timeouts.navigate_expect,
            )
            logger.info("Post-OTP redirect confirmed — now on: %s", self.page.url)
        except Exception as e:
            logger.warning("Post-OTP wait_for_url timed out or not needed: %s", e)


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

        # Wait for Scopely ID authorization portal (identified by unique placeholder)
        scopely_email_input = self.page.locator("input[placeholder*='example.com']").first
        self.expect_visible(scopely_email_input, timeout=AppConfig.timeouts.navigate_expect)
        logger.info("Entering email '%s' on Scopely ID portal", email)
        scopely_email_input.fill(email)

        scopely_continue_btn = self.page.locator("button:has-text('Continue'):visible").first
        self.expect_visible(scopely_continue_btn, timeout=AppConfig.timeouts.action)
        scopely_continue_btn.click()

    @property
    def facebook_login_button(self) -> Locator:
        return self.page.locator(
            "button:has-text('Facebook'):visible, button:has(img[alt*='facebook' i]):visible, "
            "[data-testid*='facebook' i]:visible, button:has-text('Continue with Facebook'):visible"
        ).first

    def initiate_facebook_login(self) -> None:
        """Opens login menu and triggers Facebook OAuth flow."""
        logger.info("Initiating Facebook OAuth login flow")
        self.goto("/")
        self.open_login()
        self.nav_login_button.click()
        self.expect_visible(self.facebook_login_button, timeout=AppConfig.timeouts.action)
        self.facebook_login_button.click()

    def login_with_facebook(self, email: str, password: str) -> None:
        """Automates Facebook OAuth login popup/redirect flow."""
        logger.info("Logging in via Facebook OAuth for: %s", email)
        self.initiate_facebook_login()

        # Handle Facebook OAuth form
        fb_email = self.page.locator(self.locators.FB_EMAIL_INPUT).first
        self.expect_visible(fb_email, timeout=AppConfig.timeouts.navigate_expect)
        fb_email.fill(email)

        fb_pass = self.page.locator(self.locators.FB_PASSWORD_INPUT).first
        self.expect_visible(fb_pass, timeout=AppConfig.timeouts.action)
        fb_pass.fill(password)

        fb_login_btn = self.page.locator(self.locators.FB_LOGIN_BUTTON).first
        if fb_login_btn.is_visible():
            fb_login_btn.click()

        # Handle Facebook consent / continue confirmation if displayed
        fb_continue_btn = self.page.locator(self.locators.FB_CONTINUE_BUTTON).first
        if fb_continue_btn.is_visible():
            fb_continue_btn.click()

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
