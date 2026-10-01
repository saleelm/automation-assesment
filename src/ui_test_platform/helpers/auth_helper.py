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
        # UI mode navigation
        page.goto(AppConfig.base_url, wait_until="domcontentloaded")

    # Optional session validation check
    if val_path:

        def predicate(res: Response) -> bool:
            return res.request.method == "GET" and val_path in res.url

        with page.expect_response(predicate, timeout=AppConfig.timeouts.api_route_fetch) as info:
            page.reload(wait_until="domcontentloaded")
        if info.value.status != 200:
            raise RuntimeError(f"Session validation endpoint failed with status {info.value.status}")

    # Ensure URL is within BASE_URL and not stuck on IDP
    app_host = urlparse(AppConfig.base_url).hostname
    page.wait_for_url(
        lambda url: urlparse(url).hostname == app_host and AppConfig.idp_path_marker not in urlparse(url).path,
        timeout=AppConfig.timeouts.navigate_expect,
    )

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
