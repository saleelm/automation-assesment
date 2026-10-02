from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from ui_test_platform.config.app_config import AppConfig
from ui_test_platform.helpers.interstitial_session_helper import seed_interstitial_skip_storage

if TYPE_CHECKING:
    from playwright.sync_api import BrowserContext, Page, Response

logger = logging.getLogger("ui_test_platform.helpers.auth")


def bootstrap_auth_storage_state(page: Page, context: BrowserContext) -> None:
    """Bootstraps authenticated session state for token or UI mode and persists storage state."""
    logger.info("Bootstrapping auth storage state (mode=%s)...", AppConfig.auth_mode)
    seed_interstitial_skip_storage(context)
    val_path = AppConfig.session_validation_path

    if AppConfig.auth_mode == "token":
        # API password grant via Playwright APIRequestContext
        token_url = AppConfig.auth_token_url
        response = context.request.post(
            token_url,
            form={
                "grant_type": AppConfig.auth_grant_type,
                "client_id": AppConfig.auth_client_id,
                "username": AppConfig.credentials.email,
                "password": AppConfig.credentials.password,
            },
        )
        if response.status != 200:
            raise RuntimeError(f"Token auth failed with status {response.status}: {response.text()}")

        token_data = response.json()
        access_token = token_data.get("access_token", "")
        refresh_token = token_data.get("refresh_token", "")

        # Inject into localStorage and sessionStorage via init script
        inject_script = f"""
        try {{
            window.localStorage.setItem('auth_token', {json.dumps(access_token)});
            window.localStorage.setItem('refresh_token', {json.dumps(refresh_token)});
            window.sessionStorage.setItem('auth_token', {json.dumps(access_token)});
        }} catch(e) {{}}
        """
        context.add_init_script(inject_script)
        page.goto(AppConfig.base_url, wait_until="domcontentloaded")

    else:
        # UI mode navigation & authentication
        try:
            from ui_test_platform.pages.stumbleguys.login_page import LoginPage

            login_page = LoginPage(page)
            if AppConfig.login_provider == "facebook":
                logger.info("Performing automated Facebook UI login for auth bootstrap")
                page.goto(AppConfig.base_url, wait_until="domcontentloaded")
                login_page.login_with_facebook(AppConfig.fb_user_email, AppConfig.fb_user_password)
            else:
                logger.info("Performing automated dynamic Email OTP signup/login for auth bootstrap")
                from ui_test_platform.helpers.email_otp_helper import (
                    MailServiceRateLimitError,
                    TempMailClient,
                )
                from ui_test_platform.helpers.user_credential_store import (
                    load_test_user,
                    save_test_user,
                )

                temp_mail = TempMailClient()
                try:
                    existing_user = load_test_user()

                    if existing_user:
                        # ── Returning user: skip signup, go straight to OTP login ──
                        email_addr = existing_user["email"]
                        mail_token = existing_user["mail_token"]
                        logger.info(
                            "Reusing persisted test account: %s — skipping signup flow",
                            email_addr,
                        )
                        # Record time before login so we only accept OTPs sent for
                        # this specific session — not stale ones from previous runs.
                        from datetime import UTC, datetime

                        login_initiated_at = datetime.now(tz=UTC)
                        login_page.initiate_signup_or_login(email_addr)
                        otp_code = temp_mail.wait_for_otp(
                            token=mail_token,
                            timeout_sec=45,
                            min_created_at=login_initiated_at,
                        )
                        login_page.enter_otp(otp_code)
                    else:
                        # ── New user: full signup + email verification + OTP ──
                        email_addr, mail_token = temp_mail.create_inbox()
                        logger.info("Created new test inbox: %s", email_addr)

                        # Save immediately (unverified) so a crash mid-flow is recoverable
                        save_test_user(email_addr, mail_token, verified=False)

                        login_page.initiate_signup_or_login(email_addr)
                        login_page.submit_scopely_signup_agreement()

                        email_data = temp_mail.wait_for_verification_email(token=mail_token, timeout_sec=45)
                        confirm_url = email_data.get("confirm_url")
                        if confirm_url:
                            logger.info("Visiting signup confirmation link: %s", confirm_url)
                            page.goto(confirm_url, wait_until="networkidle")

                        login_page.initiate_signup_or_login(email_addr)
                        otp_code = temp_mail.wait_for_otp(token=mail_token, timeout_sec=45)
                        login_page.enter_otp(otp_code)

                        # Mark verified only after successful OTP entry
                        save_test_user(email_addr, mail_token, verified=True)
                        logger.info("New test account created and verified: %s", email_addr)

                    page.wait_for_url(
                        lambda u: urlparse(u).hostname in ("www.stumbleguys.com", "stumbleguys.com"),
                        timeout=AppConfig.timeouts.navigate_expect,
                    )
                    login_page.dismiss_cookie_banner()
                    logger.info("Auth bootstrap completed successfully for: %s", email_addr)
                except MailServiceRateLimitError as e:
                    logger.warning("Disposable mail service rate limited during auth setup: %s", e)
                except Exception as e:
                    logger.warning("Automated email OTP signup/login step failed during bootstrap: %s", e)

        except Exception as e:
            logger.debug("Automated UI auth step skipped/deferred: %s", e)

    # Optional session validation check
    if val_path:

        def predicate(res: Response) -> bool:
            return res.request.method == "GET" and val_path in res.url

        try:
            with page.expect_response(predicate, timeout=AppConfig.timeouts.api_route_fetch) as info:
                page.reload(wait_until="domcontentloaded")
            if info.value.status != 200:
                raise RuntimeError(f"Session validation endpoint failed with status {info.value.status}")
        except Exception as e:
            logger.debug("Session validation check skipped/timed out: %s", e)

    # Ensure URL is within BASE_URL and not stuck on IDP
    try:
        app_host = urlparse(AppConfig.base_url).hostname
        page.wait_for_url(
            lambda url: urlparse(url).hostname == app_host and AppConfig.idp_path_marker not in urlparse(url).path,
            timeout=AppConfig.timeouts.navigate_expect,
        )
    except Exception as e:
        logger.debug("Post-auth wait_for_url skipped/timed out: %s", e)

    auth_path = Path("playwright/.auth/userSession.json")
    auth_path.parent.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=str(auth_path))


def ensure_fresh_auth_session(page: Page) -> None:
    """Injects or refreshes auth tokens when running in token mode. No-op in UI mode."""
    if AppConfig.auth_mode == "token":
        # Ensures token freshness in storage
        page.evaluate(
            """
            try {
                const token = window.localStorage.getItem('auth_token');
                if (token) {
                    window.sessionStorage.setItem('auth_token', token);
                }
            } catch(e) {}
            """
        )
