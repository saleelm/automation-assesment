from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from filelock import FileLock

from ui_test_platform.config.app_config import AppConfig
from ui_test_platform.enums.tags import Platform, Tag
from ui_test_platform.helpers.auth_helper import bootstrap_auth_storage_state

if TYPE_CHECKING:
    from collections.abc import Generator

    from playwright.sync_api import Browser, BrowserContext, Page, Playwright

    from ui_test_platform.helpers.appium_helper import AppiumRuntime


@pytest.fixture(scope="session")
def platform(pytestconfig: pytest.Config) -> Platform:
    val = pytestconfig.getoption("--platform") or os.getenv("PLATFORM", Platform.WEB.value)
    return Platform(val)


@pytest.fixture(scope="session")
def auth_state(playwright: Playwright, browser_type: Any) -> Path:
    """Session-scoped fixture to ensure authenticated user session exists exactly once.

    Guarded by FileLock for xdist multi-process parallel execution safety.
    """
    auth_dir = Path("playwright/.auth")
    auth_dir.mkdir(parents=True, exist_ok=True)
    state_file = auth_dir / "userSession.json"
    lock_file = auth_dir / ".lock"

    with FileLock(str(lock_file)):
        if state_file.exists() and state_file.stat().st_size > 10:
            return state_file

        browser = browser_type.launch(headless=True)
        context = browser.new_context(base_url=AppConfig.base_url)
        page = context.new_page()

        try:
            bootstrap_auth_storage_state(page, context)
        except Exception:
            # If live auth credentials fail or dummy, create valid baseline empty state
            context.storage_state(path=str(state_file))
        finally:
            context.close()
            browser.close()

    return state_file


@pytest.fixture
def browser_context_args(
    request: pytest.FixtureRequest,
    platform: Platform,
    playwright: Playwright,
    auth_state: Path,
) -> dict[str, Any]:
    """Function-scoped context arguments supporting desktop and mobile-emulation."""
    args: dict[str, Any] = {
        "base_url": AppConfig.base_url,
        "ignore_https_errors": True,
    }

    if platform == Platform.MOBILE_EMULATED:
        device_descriptor = playwright.devices.get(AppConfig.mobile_device)
        if device_descriptor:
            args.update(device_descriptor)
        else:
            args.update(
                {
                    "viewport": {"width": 390, "height": 844},
                    "user_agent": (
                        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
                    ),
                    "is_mobile": True,
                    "has_touch": True,
                }
            )
    elif platform == Platform.WEB:
        args.update({"viewport": {"width": 1280, "height": 800}})

    # Check unauthenticated marker
    unauthenticated = request.node.get_closest_marker(Tag.UNAUTHENTICATED.value) is not None
    if not unauthenticated and auth_state.exists():
        args["storage_state"] = str(auth_state)

    return args


@pytest.fixture(scope="session")
def appium_runtime(platform: Platform, playwright: Playwright) -> Generator[AppiumRuntime | None, None, None]:
    """Session-scoped Appium Chrome session with Playwright attached over CDP."""
    from ui_test_platform.helpers.appium_helper import (
        AppiumRuntime,
        create_android_chrome_driver,
        ensure_android_device,
        ensure_appium_server,
        remove_cdp_forward,
        resolve_cdp_endpoint,
    )

    if platform != Platform.ANDROID_DEVICE:
        yield None
        return

    service = None
    driver = None
    cdp_browser: Browser | None = None
    udid: str | None = None
    forwarded_port: int | None = None
    try:
        udid = ensure_android_device()
        service = ensure_appium_server()
        driver = create_android_chrome_driver(udid)
        cdp_endpoint, forwarded_port = resolve_cdp_endpoint(driver, udid)
        cdp_browser = playwright.chromium.connect_over_cdp(cdp_endpoint)
        contexts = cdp_browser.contexts
        playwright_context = contexts[0] if contexts else cdp_browser.new_context()
        playwright_context.set_default_timeout(AppConfig.timeouts.action)
        playwright_context.set_default_navigation_timeout(AppConfig.timeouts.navigation)
        yield AppiumRuntime(
            driver=driver,
            cdp_browser=cdp_browser,
            playwright_context=playwright_context,
            service=service,
            cdp_endpoint=cdp_endpoint,
            forwarded_port=forwarded_port,
        )
    finally:
        if cdp_browser is not None:
            cdp_browser.close()
        if driver is not None:
            driver.quit()
        if service is not None:
            service.stop()
        remove_cdp_forward(udid, forwarded_port)


@pytest.fixture
def context(
    request: pytest.FixtureRequest,
    browser_context_args: dict[str, Any],
    platform: Platform,
) -> Generator[BrowserContext, None, None]:
    """Provides a BrowserContext configured with timeouts and platform support."""
    if platform == Platform.ANDROID_DEVICE:
        runtime = request.getfixturevalue("appium_runtime")
        if runtime is None:
            pytest.fail("Appium runtime was not initialized for --platform android-device.")
        ctx: BrowserContext = runtime.playwright_context
        ctx.set_default_timeout(AppConfig.timeouts.action)
        ctx.set_default_navigation_timeout(AppConfig.timeouts.navigation)
        yield ctx
        return

    browser: Browser = request.getfixturevalue("browser")
    ctx = browser.new_context(**browser_context_args)
    ctx.set_default_timeout(AppConfig.timeouts.action)
    ctx.set_default_navigation_timeout(AppConfig.timeouts.navigation)
    ctx.route("**/*usercentrics*", lambda route: route.abort())
    yield ctx
    ctx.close()


@pytest.fixture
def page(context: BrowserContext) -> Generator[Page, None, None]:
    pg = context.new_page()
    yield pg
    pg.close()
