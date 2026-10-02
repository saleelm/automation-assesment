from __future__ import annotations

import json
import logging
import os
import re
import shutil
import socket
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.error import URLError
from urllib.request import urlopen

import pytest

from ui_test_platform.config.app_config import AppConfig
from ui_test_platform.helpers.async_helper import poll_condition

if TYPE_CHECKING:
    from appium.webdriver.appium_service import AppiumService
    from appium.webdriver.webdriver import WebDriver
    from playwright.sync_api import Browser, BrowserContext

logger = logging.getLogger("ui_test_platform.appium")

_SERIAL_PATTERN = re.compile(r"^[A-Za-z0-9._:-]+$")


@dataclass
class AppiumRuntime:
    """Holds the Appium session and the Playwright browser attached over CDP."""

    driver: WebDriver
    cdp_browser: Browser
    playwright_context: BrowserContext
    service: AppiumService | None
    cdp_endpoint: str
    forwarded_port: int | None = None


def _find_free_port() -> int:
    """Finds an available TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def is_appium_ready(server_url: str) -> bool:
    """Returns True when the Appium /status endpoint responds successfully."""
    try:
        with urlopen(f"{server_url.rstrip('/')}/status", timeout=2) as response:
            return bool(200 <= int(response.status) < 300)
    except (OSError, URLError, ValueError):
        return False


def ensure_adb_available() -> str:
    """Resolves the adb binary or fails with a setup hint."""
    adb_path = shutil.which("adb")
    if adb_path is not None:
        return adb_path

    # Fallback to standard ANDROID_HOME / standard SDK locations
    home = Path.home()
    candidates = [
        os.environ.get("ANDROID_HOME", "") + "/platform-tools/adb",
        os.environ.get("ANDROID_SDK_ROOT", "") + "/platform-tools/adb",
        str(home / "Library" / "Android" / "sdk" / "platform-tools" / "adb"),
        str(home / "Android" / "Sdk" / "platform-tools" / "adb"),
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate

    pytest.fail(
        "adb was not found on PATH. Install Android platform-tools (`brew install android-platform-tools` on macOS) "
        "and connect a device/emulator before running `--platform android-device`."
    )


def list_adb_serials(adb_path: str) -> list[str]:
    """Returns serials reported by `adb devices` in the device/emulator state."""
    completed = subprocess.run(  # noqa: S603
        [adb_path, "devices"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        pytest.fail(f"adb devices failed: {completed.stderr.strip() or completed.stdout.strip()}")

    serials: list[str] = []
    for line in completed.stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            serials.append(parts[0])
    return serials


def ensure_android_device() -> str | None:
    """Fails fast when no adb device is connected; returns the configured or first serial."""
    adb_path = ensure_adb_available()
    serials = list_adb_serials(adb_path)
    if not serials:
        pytest.fail(
            "No Android device/emulator was found via adb. Start an emulator or plug in a device "
            "with USB debugging, or use `--platform mobile-emulated`."
        )
    configured = AppConfig.android_serial
    if configured:
        if not _SERIAL_PATTERN.fullmatch(configured):
            pytest.fail("ANDROID_SERIAL contains invalid characters.")
        if configured not in serials:
            pytest.fail(f"ANDROID_SERIAL={configured} is not connected. Available devices: {', '.join(serials)}")
        return configured
    return serials[0]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _resolve_appium_bin() -> str | None:
    local_bin = _repo_root() / "node_modules" / ".bin" / "appium"
    if local_bin.is_file():
        return str(local_bin)
    return shutil.which("appium")


def _appium_process_env() -> dict[str, str]:
    env = os.environ.copy()
    local_bin_dir = _repo_root() / "node_modules" / ".bin"
    if local_bin_dir.is_dir():
        env["PATH"] = f"{local_bin_dir}{os.pathsep}{env.get('PATH', '')}"
    return env


def ensure_appium_server() -> AppiumService | None:
    """Connects to a running Appium server, or starts one locally when APPIUM_AUTO_START=true."""
    server_url = AppConfig.appium_server_url
    if is_appium_ready(server_url):
        logger.info("Using existing Appium server at %s", server_url)
        return None

    if not AppConfig.appium_auto_start:
        pytest.fail(
            f"Appium is not reachable at {server_url}. Start it with `make appium` or set APPIUM_AUTO_START=true."
        )

    if _resolve_appium_bin() is None:
        pytest.fail(
            "Appium CLI was not found on PATH. Run `make install-appium` "
            "(requires Node.js) then retry `--platform android-device`."
        )

    from appium.webdriver.appium_service import AppiumService

    logger.info("Starting Appium server at %s", server_url)
    service = AppiumService()
    service.start(
        args=[
            "--address",
            AppConfig.appium_host,
            "--port",
            str(AppConfig.appium_port),
            "--allow-insecure",
            "chromedriver_autodownload",
        ],
        env=_appium_process_env(),
        timeout_ms=AppConfig.timeouts.slow_render,
    )
    poll_condition(
        lambda: server_url if is_appium_ready(server_url) else None,
        timeout_ms=AppConfig.timeouts.slow_render,
        interval_ms=250,
    )
    return service


def create_android_chrome_driver(udid: str | None) -> WebDriver:
    """Creates an Appium UiAutomator2 session against Chrome on the attached Android device."""
    from appium import webdriver
    from appium.options.android import UiAutomator2Options

    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.device_name = AppConfig.android_device_name
    options.browser_name = "Chrome"
    options.no_reset = True
    options.new_command_timeout = 300
    if udid:
        options.udid = udid
    options.set_capability(
        "appium:chromeOptions",
        {
            "androidPackage": AppConfig.android_chrome_package,
            "args": ["--disable-fre", "--no-first-run", "--disable-popup-blocking"],
        },
    )
    options.set_capability("appium:autoGrantPermissions", True)
    options.set_capability("appium:ensureWebviewsHavePages", True)
    options.set_capability("appium:nativeWebScreenshot", True)

    logger.info("Creating Appium Chrome session against %s", AppConfig.appium_server_url)
    driver = webdriver.Remote(command_executor=AppConfig.appium_server_url, options=options)
    driver.implicitly_wait(0)
    return driver


def resolve_cdp_endpoint(driver: WebDriver, udid: str | None) -> tuple[str, int | None]:
    """Resolves a Playwright-compatible CDP HTTP endpoint for the Appium Chrome session."""
    caps: dict[str, Any] = dict(driver.capabilities)
    chrome_options = caps.get("goog:chromeOptions")
    if isinstance(chrome_options, dict):
        debugger_address = chrome_options.get("debuggerAddress")
        if isinstance(debugger_address, str) and debugger_address.strip():
            address = debugger_address.strip()
            endpoint = address if address.startswith("http") else f"http://{address}"
            _wait_for_cdp(endpoint)
            return endpoint, None

    se_cdp = caps.get("se:cdp")
    if isinstance(se_cdp, str) and se_cdp.startswith(("ws://", "wss://")):
        # Playwright connect_over_cdp expects an HTTP browser URL; derive host:port from the WS URL.
        without_scheme = se_cdp.split("://", 1)[1]
        hostport = without_scheme.split("/", 1)[0]
        endpoint = f"http://{hostport}"
        _wait_for_cdp(endpoint)
        return endpoint, None

    return _forward_chrome_devtools(udid)


def _forward_chrome_devtools(udid: str | None) -> tuple[str, int]:
    adb_path = ensure_adb_available()
    custom_port = os.getenv("APPIUM_CDP_PORT")
    port = int(custom_port) if custom_port else _find_free_port()

    command = [adb_path]
    if udid:
        command.extend(["-s", udid])
    command.extend(["forward", f"tcp:{port}", "localabstract:chrome_devtools_remote"])
    completed = subprocess.run(command, check=False, capture_output=True, text=True)  # noqa: S603
    if completed.returncode != 0:
        # If the port was in use, retry with a dynamically allocated free port
        port = _find_free_port()
        command = [adb_path]
        if udid:
            command.extend(["-s", udid])
        command.extend(["forward", f"tcp:{port}", "localabstract:chrome_devtools_remote"])
        completed = subprocess.run(command, check=False, capture_output=True, text=True)  # noqa: S603

    if completed.returncode != 0:
        pytest.fail(f"Failed to adb-forward Chrome DevTools. {completed.stderr.strip() or completed.stdout.strip()}")
    endpoint = f"http://127.0.0.1:{port}"
    _wait_for_cdp(endpoint)
    return endpoint, port


def _wait_for_cdp(endpoint: str) -> None:
    def _ready() -> str | None:
        try:
            with urlopen(f"{endpoint.rstrip('/')}/json/version", timeout=2) as response:
                if 200 <= int(response.status) < 300:
                    payload = json.loads(response.read().decode("utf-8"))
                    if isinstance(payload, dict):
                        return endpoint
        except (OSError, URLError, ValueError, json.JSONDecodeError):
            return None
        return None

    poll_condition(_ready, timeout_ms=AppConfig.timeouts.slow_render, interval_ms=250)


def remove_cdp_forward(udid: str | None, port: int | None = None) -> None:
    """Best-effort cleanup of the local adb CDP port forward."""
    adb_path = shutil.which("adb")
    if adb_path is None:
        return
    command = [adb_path]
    if udid:
        command.extend(["-s", udid])
    target_port = port or AppConfig.appium_cdp_port
    command.extend(["forward", "--remove", f"tcp:{target_port}"])
    subprocess.run(command, check=False, capture_output=True, text=True)  # noqa: S603
