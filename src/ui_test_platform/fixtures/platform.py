from __future__ import annotations

import contextlib
import logging
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

logger = logging.getLogger("ui_test_platform.runner")


@pytest.fixture(scope="session")
def platform(pytestconfig: pytest.Config) -> Platform:
    val = pytestconfig.getoption("--platform") or os.getenv("PLATFORM", Platform.WEB.value)
    return Platform(val)


@pytest.fixture(scope="session")
def auth_state(playwright: Playwright, browser_type: Any, pytestconfig: pytest.Config) -> Path:
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

        # Respect --headed flag: run bootstrap browser visibly so we can observe the
        # OTP flow and avoid Scopely's headless bot-detection heuristics.
        headed = pytestconfig.getoption("--headed", default=False)
        browser = browser_type.launch(headless=not headed)
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

    video_opt = request.config.getoption("--video", default="off")
    if video_opt in ("on", "retain-on-failure"):
        videos_dir = Path("videos")
        videos_dir.mkdir(parents=True, exist_ok=True)
        args["record_video_dir"] = str(videos_dir)

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

    pages: list[Page] = list(ctx.pages)
    ctx.on("page", lambda p: pages.append(p))

    yield ctx

    ctx.close()

    video_opt = request.config.getoption("--video", default="off")
    if video_opt in ("on", "retain-on-failure"):
        rep_call = getattr(request.node, "rep_call", None)
        rep_setup = getattr(request.node, "rep_setup", None)
        is_failed = (rep_call is not None and rep_call.failed) or (rep_setup is not None and rep_setup.failed)

        videos_dir = Path("videos")
        videos_dir.mkdir(parents=True, exist_ok=True)
        safe_name = request.node.nodeid.replace("/", "_").replace("::", "__").replace("[", "_").replace("]", "")

        for index, pg in enumerate(pages):
            video = pg.video
            if not video:
                continue

            try:
                raw_path = Path(video.path())
            except Exception as e:
                logger.debug("Failed to determine video path: %s", e)
                continue

            if is_failed:
                suffix = f"_{index + 1}" if len(pages) > 1 else ""
                dest_path = videos_dir / f"{safe_name}{suffix}.webm"
                try:
                    video.save_as(str(dest_path))
                    if raw_path != dest_path and raw_path.exists():
                        raw_path.unlink(missing_ok=True)
                    logger.error("🎥 Failure video saved at: %s", dest_path)

                    with contextlib.suppress(Exception):
                        import allure

                        allure.attach.file(  # type: ignore[no-untyped-call]
                            str(dest_path),
                            name=f"Failure Video: {request.node.name}",
                            attachment_type=allure.attachment_type.WEBM,
                        )
                except Exception as e:
                    logger.debug("Failed to save or attach failure video: %s", e)
            elif video_opt == "retain-on-failure":
                with contextlib.suppress(Exception):
                    video.delete()


@pytest.fixture
def page(context: BrowserContext) -> Generator[Page, None, None]:
    pg = context.new_page()
    yield pg
    pg.close()
