from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ui_test_platform.enums.tags import Platform, Tag
from ui_test_platform.helpers.auth_helper import ensure_fresh_auth_session
from ui_test_platform.helpers.interstitial_session_helper import seed_interstitial_skip_storage
from ui_test_platform.pages.stumbleguys.home_page import HomePage
from ui_test_platform.pages.stumbleguys.login_page import LoginPage
from ui_test_platform.pages.stumbleguys.shop_page import ShopPage
from ui_test_platform.pages.stumbleguys.webgl_game_page import WebGLGamePage

if TYPE_CHECKING:
    from playwright.sync_api import BrowserContext, Page


# Auto fixtures with explicit dependency chain
@pytest.fixture(autouse=True)
def _ensure_auth_session(request: pytest.FixtureRequest, page: Page) -> None:
    unauthenticated = request.node.get_closest_marker(Tag.UNAUTHENTICATED.value) is not None
    if not unauthenticated:
        ensure_fresh_auth_session(page)


@pytest.fixture(autouse=True)
def _sync_session_storage(_ensure_auth_session: None, context: BrowserContext) -> None:
    context.add_init_script(
        """
        try {
            const token = window.localStorage.getItem('auth_token');
            if (token) {
                window.sessionStorage.setItem('auth_token', token);
            }
        } catch(e) {}
        """
    )


@pytest.fixture(autouse=True)
def _seed_interstitial_state(
    request: pytest.FixtureRequest,
    _sync_session_storage: None,
    context: BrowserContext,
) -> None:
    gate_marker = request.node.get_closest_marker(Tag.INTERSTITIAL_GATE.value) is not None
    if not gate_marker:
        seed_interstitial_skip_storage(context)


# Page Object fixtures
@pytest.fixture
def home_page(page: Page, platform: Platform) -> HomePage:
    return HomePage(page=page, platform=platform)


@pytest.fixture
def login_page(page: Page, platform: Platform) -> LoginPage:
    return LoginPage(page=page, platform=platform)


@pytest.fixture
def shop_page(page: Page, platform: Platform) -> ShopPage:
    return ShopPage(page=page, platform=platform)


@pytest.fixture
def game_page(page: Page, platform: Platform) -> WebGLGamePage:
    return WebGLGamePage(page=page, platform=platform)
