from __future__ import annotations

import os
from dataclasses import dataclass
from typing import NamedTuple


class ConfigError(Exception):
    """Raised when a required configuration value is missing at access time."""


class UserCredentials(NamedTuple):
    email: str
    password: str


@dataclass(frozen=True)
class Timeouts:
    navigation: int = 30_000
    action: int = 15_000
    expect: int = 20_000
    navigate_expect: int = 40_000
    slow_render: int = 60_000
    game_download: int = 180_000
    api_route_fetch: int = 60_000
    long_operation: int = 600_000


class _AppConfig:
    """Runtime configuration singleton.

    Missing required properties raise ConfigError on access, not at import time.
    """

    timeouts: Timeouts = Timeouts()

    @property
    def environment(self) -> str:
        return os.getenv("ENVIRONMENT", "qa").strip()

    @property
    def platform(self) -> str:
        return os.getenv("PLATFORM", "web").strip()

    @property
    def base_url(self) -> str:
        val = os.getenv("BASE_URL", "https://www.stumbleguys.com").strip()
        if not val:
            raise ConfigError("BASE_URL is not set.")
        return val

    @property
    def api_url(self) -> str:
        return os.getenv("API_URL", "https://api.stumbleguys.com").strip()

    @property
    def auth_mode(self) -> str:
        return os.getenv("AUTH_MODE", "ui").strip().lower()

    @property
    def login_provider(self) -> str:
        return os.getenv("LOGIN_PROVIDER", "email").strip().lower()

    @property
    def test_user_email(self) -> str:
        val = os.getenv("TEST_USER_EMAIL")
        if not val:
            raise ConfigError("TEST_USER_EMAIL is required but missing.")
        return val.strip()

    @property
    def test_user_password(self) -> str:
        val = os.getenv("TEST_USER_PASSWORD")
        if not val:
            raise ConfigError("TEST_USER_PASSWORD is required but missing.")
        return val.strip()

    @property
    def credentials(self) -> UserCredentials:
        return UserCredentials(email=self.test_user_email, password=self.test_user_password)

    @property
    def fb_user_email(self) -> str:
        val = os.getenv("FB_USER_EMAIL") or os.getenv("TEST_USER_FB_EMAIL")
        if not val:
            raise ConfigError("FB_USER_EMAIL is required when LOGIN_PROVIDER=facebook.")
        return val.strip()

    @property
    def fb_user_password(self) -> str:
        val = os.getenv("FB_USER_PASSWORD") or os.getenv("TEST_USER_FB_PASSWORD")
        if not val:
            raise ConfigError("FB_USER_PASSWORD is required when LOGIN_PROVIDER=facebook.")
        return val.strip()

    @property
    def fb_credentials(self) -> UserCredentials:
        return UserCredentials(email=self.fb_user_email, password=self.fb_user_password)

    @property
    def auth_issuer_url(self) -> str:
        val = os.getenv("AUTH_ISSUER_URL")
        if not val:
            raise ConfigError("AUTH_ISSUER_URL is required but missing.")
        return val.strip()

    @property
    def auth_token_url(self) -> str:
        override = os.getenv("AUTH_TOKEN_URL")
        if override:
            return override.strip()
        return f"{self.auth_issuer_url.rstrip('/')}/protocol/openid-connect/token"

    @property
    def auth_client_id(self) -> str:
        val = os.getenv("AUTH_CLIENT_ID")
        if not val and self.auth_mode == "token":
            raise ConfigError("AUTH_CLIENT_ID is required when AUTH_MODE=token.")
        return (val or "").strip()

    @property
    def auth_grant_type(self) -> str:
        return os.getenv("AUTH_GRANT_TYPE", "password").strip()

    @property
    def idp_path_marker(self) -> str:
        return os.getenv("IDP_PATH_MARKER", "/login").strip()

    @property
    def session_validation_path(self) -> str | None:
        val = os.getenv("SESSION_VALIDATION_PATH", "").strip()
        return val if val else None

    @property
    def mobile_device(self) -> str:
        return os.getenv("MOBILE_DEVICE", "Pixel 7").strip()

    @property
    def android_serial(self) -> str | None:
        val = os.getenv("ANDROID_SERIAL", "").strip()
        return val if val else None

    @property
    def android_chrome_package(self) -> str:
        return os.getenv("ANDROID_CHROME_PACKAGE", "com.android.chrome").strip()

    @property
    def android_device_name(self) -> str:
        return os.getenv("ANDROID_DEVICE_NAME", "Android").strip()

    @property
    def appium_host(self) -> str:
        return os.getenv("APPIUM_HOST", "127.0.0.1").strip()

    @property
    def appium_port(self) -> int:
        return int(os.getenv("APPIUM_PORT", "4723"))

    @property
    def appium_server_url(self) -> str:
        override = os.getenv("APPIUM_SERVER_URL", "").strip()
        if override:
            return override.rstrip("/")
        return f"http://{self.appium_host}:{self.appium_port}"

    @property
    def appium_cdp_port(self) -> int:
        return int(os.getenv("APPIUM_CDP_PORT", "9222"))

    @property
    def appium_auto_start(self) -> bool:
        return os.getenv("APPIUM_AUTO_START", "true").strip().lower() in {"1", "true", "yes"}

    @property
    def configured_context_option(self) -> str | None:
        val = os.getenv("CONTEXT_OPTION", "").strip()
        return val if val else None

    @property
    def workers(self) -> int:
        return int(os.getenv("WORKERS", "1"))

    @property
    def testrail_enabled(self) -> bool:
        return os.getenv("TESTRAIL_ENABLED", "false").lower() == "true"


AppConfig = _AppConfig()
