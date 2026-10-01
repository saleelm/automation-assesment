from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ui_test_platform.config.app_config import AppConfig
from ui_test_platform.enums.tags import Platform
from ui_test_platform.pages.base_page import BasePage

if TYPE_CHECKING:
    from playwright.sync_api import FloatRect, Locator, Page

logger = logging.getLogger("ui_test_platform.pages.webgl")


class WebGLGamePage(BasePage):
    """Page Object for Stumble Guys WebGL Unity Browser Game portal (/play)."""

    def __init__(self, page: Page, platform: Platform = Platform.WEB) -> None:
        super().__init__(page, platform)

    @property
    def player_container(self) -> Locator:
        return self.page.locator("#player")

    @property
    def game_loader(self) -> Locator:
        return self.page.locator("[class*='Loader_loader'], img[alt='Running stumbler']")

    @property
    def game_canvas(self) -> Locator:
        return self.page.locator("#player canvas, canvas#unity-canvas, canvas").first

    def navigate(self) -> WebGLGamePage:
        """Navigates to the /play WebGL game portal."""
        logger.info("Navigating to WebGL Game Portal (/play)")
        self.goto("/play")
        self.expect_visible(self.player_container, timeout=AppConfig.timeouts.navigate_expect)
        return self

    def is_webgl_supported(self) -> bool:
        """Evaluates browser WebGL context availability on the canvas."""
        logger.info("Evaluating WebGL2/WebGL context availability in browser engine")
        result: bool = self.page.evaluate(
            """
            () => {
                const canvas = document.createElement('canvas');
                const gl = canvas.getContext('webgl2')
                    || canvas.getContext('webgl')
                    || canvas.getContext('experimental-webgl');
                return !!gl;
            }
            """
        )
        return result

    def get_canvas_bounding_box(self) -> FloatRect | None:
        """Retrieves active canvas bounding dimensions for coordinate-based interactions."""
        box: FloatRect | None = self.player_container.bounding_box()
        return box

    def dispatch_canvas_click(self, relative_x: float = 0.5, relative_y: float = 0.5) -> None:
        """Clicks at proportional coordinates within the WebGL canvas viewport."""
        logger.info("Dispatching canvas viewport click at relative (%.2f, %.2f)", relative_x, relative_y)
        box = self.get_canvas_bounding_box()
        if box:
            click_x = box["x"] + (box["width"] * relative_x)
            click_y = box["y"] + (box["height"] * relative_y)
            self.page.mouse.click(click_x, click_y)

    def dispatch_gameplay_keys(self, keys: list[str]) -> None:
        """Dispatches keyboard inputs (e.g. Space, W, A, S, D, Arrow keys) to the focused game canvas."""
        logger.info("Dispatching gameplay keys: %s", keys)
        for key in keys:
            self.page.keyboard.press(key)
