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


@pytest.fixture
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


@pytest.fixture
def context(
    request: pytest.FixtureRequest,
    browser: Browser,
    browser_context_args: dict[str, Any],
    platform: Platform,
    playwright: Playwright,
) -> Generator[BrowserContext, None, None]:
    """Provides a BrowserContext configured with timeouts and platform support."""
    if platform == Platform.ANDROID_DEVICE:
        android_api = getattr(playwright, "android", None)
        if android_api is None or not hasattr(android_api, "devices"):
            pytest.fail(
                "Playwright Android API is not available in the current environment. "
                "Ensure adb is installed or use '--platform mobile-emulated'."
            )
        android_devices = android_api.devices()
        if not android_devices:
            pytest.fail(
                "Platform is set to 'android-device' but no Android device/emulator was found via adb. "
                "Ensure an adb device is connected or use '--platform mobile-emulated'."
            )
        target_serial = AppConfig.android_serial
        device = (
            next((d for d in android_devices if d.serial == target_serial), android_devices[0])
            if target_serial
            else android_devices[0]
        )
        ctx = device.launch_browser(pkg=AppConfig.android_chrome_package)
        ctx.set_default_timeout(AppConfig.timeouts.action)
        ctx.set_default_navigation_timeout(AppConfig.timeouts.navigation)
        yield ctx
        ctx.close()
        device.close()
        return

    ctx = browser.new_context(**browser_context_args)
    ctx.set_default_timeout(AppConfig.timeouts.action)
    ctx.set_default_navigation_timeout(AppConfig.timeouts.navigation)
    yield ctx
    ctx.close()


@pytest.fixture
def page(context: BrowserContext) -> Generator[Page, None, None]:
    pg = context.new_page()
    yield pg
    pg.close()
