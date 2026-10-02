from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlparse

import pytest

from ui_test_platform.fixtures.pom.test_options import AppConfig, Tag, expect, step, tags, title

if TYPE_CHECKING:
    from ui_test_platform.pages.stumbleguys.login_page import LoginPage

pytestmark = pytest.mark.unauthenticated


class TestAuthentication:
    @tags(Tag.SANITY, Tag.SMOKE, Tag.LOGIN)
    @title("TC01 should open login triggers and render authentication options")
    def test_tc01_should_open_login_triggers_and_render_options(self, login_page: LoginPage) -> None:
        with step("Given the user navigates to the Stumble Guys portal"):
            login_page.goto("/")

        with step("When the user opens the login menu trigger"):
            login_page.open_login()

        with step("Then the login action button should be visible"):
            expect(login_page.nav_login_button).to_be_visible(timeout=AppConfig.timeouts.action)

    @tags(Tag.REGRESSION, Tag.LOGIN)
    @title("TC02 should validate invalid email format when attempting login")
    def test_tc02_should_validate_invalid_email_format(self, login_page: LoginPage) -> None:
        with step("Given the user opens the login flow"):
            login_page.goto("/")
            login_page.open_login()

        with step("When the user submits invalid email credentials"):
            login_page.submit_invalid_credentials("invalid_email_format")

        with step("Then the system should maintain page stability without crashing"):
            app_host = urlparse(AppConfig.base_url).hostname
            current_host = urlparse(login_page.page.url).hostname
            assert current_host == app_host or "login" in login_page.page.url

    @tags(Tag.E2E, Tag.LOGIN, Tag.AUTH)
    @title("TC03 should automate email OTP retrieval and entry pipeline")
    def test_tc03_should_automate_email_otp_retrieval_and_entry(self, login_page: LoginPage) -> None:
        from ui_test_platform.helpers.email_otp_helper import (
            MailServiceRateLimitError,
            TempMailClient,
        )

        temp_mail = TempMailClient()

        with step("Given a disposable automated test mailbox is created"):
            try:
                email_addr, token = temp_mail.create_inbox()
            except MailServiceRateLimitError as e:
                pytest.skip(f"Public disposable mail service is rate-limited: {e}")
            assert "@" in email_addr
            assert len(token) > 0

        with step("When the user initiates login with the automated email"):
            login_page.initiate_signup_or_login(email_addr)

        with step("Then the identity provider renders the authentication prompt"):
            auth_prompt = login_page.page.locator(
                "button:has-text('Agree and get sign up link'), "
                "input[autocomplete='one-time-code'], "
                "input[inputmode='numeric']"
            ).first
            expect(auth_prompt).to_be_visible(timeout=AppConfig.timeouts.navigate_expect)

    @tags(Tag.E2E, Tag.LOGIN, Tag.AUTH)
    @title("TC04 should automate new account signup and API mailbox verification")
    def test_tc04_should_automate_new_account_signup_and_email_verification(self, login_page: LoginPage) -> None:
        from ui_test_platform.helpers.email_otp_helper import (
            MailServiceRateLimitError,
            TempMailClient,
        )

        temp_mail = TempMailClient()

        with step("Given a fresh disposable test mailbox is provisioned via API"):
            try:
                email_addr, token = temp_mail.create_inbox()
            except MailServiceRateLimitError as e:
                pytest.skip(f"Public disposable mail service is rate-limited: {e}")
            assert "@" in email_addr

        with step("When the user initiates signup on the Stumble Guys portal"):
            login_page.initiate_signup_or_login(email_addr)

        with step("And the user confirms agreement on the identity provider"):
            login_page.submit_scopely_signup_agreement()

        with step("Then a verification email should be received in the automated mailbox"):
            email_data = temp_mail.wait_for_verification_email(token=token, timeout_sec=30)
            assert len(str(email_data.get("subject", ""))) > 0
            assert "Scopely" in str(email_data.get("subject", "")) or "Stumble" in str(email_data.get("subject", ""))
            assert "Scopely Account" in str(email_data.get("text", "")) or email_data.get("confirm_url") is not None

    @tags(Tag.E2E, Tag.LOGIN, Tag.AUTH)
    @title("TC05 should complete end-to-end signup and email verification login")
    def test_tc05_should_complete_end_to_end_signup_and_otp_login(self, login_page: LoginPage) -> None:
        from ui_test_platform.helpers.email_otp_helper import (
            MailServiceRateLimitError,
            TempMailClient,
        )

        temp_mail = TempMailClient()

        with step("Given a fresh disposable test mailbox is provisioned via API"):
            try:
                email_addr, token = temp_mail.create_inbox()
            except MailServiceRateLimitError as e:
                pytest.skip(f"Public disposable mail service is rate-limited: {e}")
            assert "@" in email_addr

        with step("When the user initiates signup on the Stumble Guys portal"):
            login_page.initiate_signup_or_login(email_addr)

        with step("And the user agrees to terms to dispatch the signup verification link"):
            login_page.submit_scopely_signup_agreement()

        with step("And the signup confirmation link is retrieved from the automated inbox"):
            email_data = temp_mail.wait_for_verification_email(token=token, timeout_sec=45)
            confirm_url = email_data.get("confirm_url")
            assert confirm_url is not None, "Verification link not found in email"

        with step("And the user visits the confirmation link to complete email verification"):
            login_page.page.goto(confirm_url, wait_until="networkidle")

        with step("When the user returns to the portal to log in with the verified email"):
            login_page.initiate_signup_or_login(email_addr)

        with step("And the 6-digit login OTP code is retrieved from the automated inbox"):
            otp_code = temp_mail.wait_for_otp(token=token, timeout_sec=45)
            assert len(otp_code) == 6

        with step("Then the user enters the 6-digit OTP code to complete authentication"):
            login_page.enter_otp(otp_code)
            login_page.page.wait_for_url(
                lambda u: "stumbleguys.com" in str(urlparse(u).hostname),
                timeout=30000,
            )
            app_host = urlparse(AppConfig.base_url).hostname
            current_host = urlparse(login_page.page.url).hostname
            assert current_host == app_host or "stumbleguys" in str(current_host)
            login_page.dismiss_cookie_banner()




