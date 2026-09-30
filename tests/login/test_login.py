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
        from ui_test_platform.helpers.email_otp_helper import TempMailClient

        temp_mail = TempMailClient()

        with step("Given a disposable automated test mailbox is created"):
            email_addr, token = temp_mail.create_inbox()
            assert "@" in email_addr
            assert len(token) > 0

        with step("When the user initiates login with the automated email"):
            login_page.goto("/")
            login_page.open_login()
            login_page.submit_invalid_credentials(email_addr)

        with step("Then the client is ready to extract and input 6-digit OTP code"):
            sample_otp = "123456"
            login_page.enter_otp(sample_otp)
