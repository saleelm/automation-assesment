from __future__ import annotations

import io
import logging
from typing import TYPE_CHECKING

from PIL import Image

from ui_test_platform.config.app_config import AppConfig
from ui_test_platform.enums.tags import Platform
from ui_test_platform.helpers.async_helper import poll_condition
from ui_test_platform.pages.base_page import BasePage

if TYPE_CHECKING:
    from playwright.sync_api import FloatRect, Locator, Page

logger = logging.getLogger("ui_test_platform.pages.webgl")


class WebGLGamePage(BasePage):
    """Page Object for Stumble Guys WebGL Unity Browser Game portal (/play)."""

    def __init__(self, page: Page, platform: Platform = Platform.WEB) -> None:
        super().__init__(page, platform)
        self._scopely_splash_seen: bool = False

    @property
    def player_container(self) -> Locator:
        return self.page.locator("div:has(> canvas), div:has(> canvas#react-unity-webgl-canvas-1), #player").first

    @property
    def game_loader(self) -> Locator:
        return self.page.locator("[class*='Loader_loader'], img[alt='Running stumbler']").first

    @property
    def game_canvas(self) -> Locator:
        return self.page.locator(
            "canvas#react-unity-webgl-canvas-1, canvas[class*='Play_canvas'], #player canvas, canvas"
        ).first

    @property
    def fullscreen_button(self) -> Locator:
        return self.page.locator(
            "button:has(img[alt='Fullscreen']), button[class*='Fullscreen_fullscreen'], img[alt='Fullscreen']"
        ).first

    @property
    def nav_play_button(self) -> Locator:
        return self.page.locator(
            "nav a[href='/play'], header a[href='/play'], a[href='/play']:visible, "
            "header button:has-text('PLAY'), nav button:has-text('PLAY')"
        ).first

    @property
    def download_button(self) -> Locator:
        return self.page.locator(
            "button:has-text('Download'), button:has-text('DOWNLOAD'), [data-testid*='download']"
        ).first

    def navigate(self) -> WebGLGamePage:
        """Navigates to the /play WebGL game portal."""
        logger.info("Navigating to WebGL Game Portal (/play)")
        self.goto("/play")
        self.expect_visible(
            self.game_loader.or_(self.game_canvas).first,
            timeout=AppConfig.timeouts.navigate_expect,
        )
        return self

    def wait_for_game_download_and_load(self, timeout: int | None = None) -> WebGLGamePage:
        """Prerequisite: waits for game loading, triggers download if prompted, and waits for WebGL assets to load."""
        max_wait = timeout or AppConfig.timeouts.game_download
        logger.info("Waiting for WebGL game loading and downloading prerequisite to complete (timeout=%sms)", max_wait)

        # 1. Click download button if a download prompt is presented
        try:
            if self.download_button.is_visible(timeout=3_000):
                logger.info("Download prompt detected; clicking download button")
                self.download_button.click()
        except Exception:
            pass

        # 2. Wait for game loader (running stumbler / percentage bar) to finish and detach
        if self.game_loader.count() > 0:
            logger.info("Waiting for game loader to finish and detach...")
            self.game_loader.wait_for(state="detached", timeout=max_wait)

        # 3. Ensure game canvas is visible
        self.expect_visible(self.game_canvas, timeout=max_wait)

        # 4. Wait for WebGL canvas to have valid dimensions and active rendering
        self.page.wait_for_function(
            """() => {
                const canvas = document.querySelector('canvas#react-unity-webgl-canvas-1, canvas');
                return canvas && canvas.width > 0 && canvas.height > 0;
            }""",
            timeout=max_wait,
        )

        self._scopely_splash_seen = self._check_scopely_blue()

        logger.info("Game loading and asset download complete. Canvas is ready.")
        return self

    def _check_scopely_blue(self) -> bool:
        """Internal check for the dominant Scopely blue canvas backdrop."""
        try:
            screenshot_bytes = self.page.screenshot()
            img = Image.open(io.BytesIO(screenshot_bytes))
            pixels = img.load()
            if pixels is None:
                return False
            w, h = img.size
            scopely_blue_count = 0
            for x in range(int(w * 0.3), int(w * 0.7), 2):
                for y in range(int(h * 0.2), int(h * 0.8), 2):
                    r, g, b, *_ = pixels[x, y]
                    if r < 35 and 100 < g < 170 and b > 210:
                        scopely_blue_count += 1
            return scopely_blue_count > 5000
        except Exception:
            return False

    def is_scopely_splash_displayed(self) -> bool:
        """Verifies if the WebGL game displayed the initial SCOPELY splash screen."""
        return self._scopely_splash_seen or self._check_scopely_blue()

    def is_welcome_aboard_displayed(self) -> bool:
        """Checks if the WELCOME ABOARD modal (with START PLAYING button) is currently rendered on canvas."""
        try:
            screenshot_bytes = self.page.screenshot()
            img = Image.open(io.BytesIO(screenshot_bytes))
            pixels = img.load()
            if pixels is None:
                return False
            w, h = img.size
            gold_button_count = 0
            for x in range(int(w * 0.4), int(w * 0.6), 2):
                for y in range(int(h * 0.45), int(h * 0.58), 2):
                    r, g, b, *_ = pixels[x, y]
                    if r > 220 and 140 < g < 215 and b < 110:
                        gold_button_count += 1
            return gold_button_count > 100
        except Exception:
            return False

    def wait_for_welcome_aboard_modal(self, timeout_ms: int = 60_000) -> bool:
        """Waits until the WebGL game transitions past SCOPELY splash and renders the WELCOME ABOARD modal."""
        logger.info("Waiting for WebGL game to transition past SCOPELY splash to WELCOME ABOARD modal...")
        try:
            poll_condition(
                lambda: True if self.is_welcome_aboard_displayed() else None,
                timeout_ms=timeout_ms,
                interval_ms=500,
            )
            logger.info("WELCOME ABOARD modal detected on WebGL canvas")
            return True
        except TimeoutError:
            raise TimeoutError(f"WELCOME ABOARD modal did not appear within {timeout_ms}ms on WebGL canvas") from None

    wait_for_in_game_play_button = wait_for_welcome_aboard_modal

    def is_direct_play_button_displayed(self) -> bool:
        """Checks if the direct PLAY button (main game lobby play button) is currently rendered on canvas."""
        if not self.is_canvas_rendered():
            return False

        if self.is_welcome_aboard_displayed():
            return False

        try:
            screenshot_bytes = self.page.screenshot()
            img = Image.open(io.BytesIO(screenshot_bytes))
            pixels = img.load()
            if pixels is None:
                return False
            w, h = img.size

            # In Stumble Guys lobby, the prominent PLAY button sits in bottom right (~75%-95% w, ~78%-95% h)
            play_btn_pixels = 0
            for x in range(int(w * 0.75), int(w * 0.95), 2):
                for y in range(int(h * 0.78), int(h * 0.95), 2):
                    r, g, b, *_ = pixels[x, y]
                    # Vibrant green or gold/yellow button colors
                    if (g > 180 and b < 100) or (r > 200 and g > 160 and b < 80):
                        play_btn_pixels += 1

            if play_btn_pixels > 50:
                return True

            # Also check if any DOM play button exists
            dom_play = self.page.locator("button:has-text('PLAY'), a:has-text('PLAY NOW')").first
            if dom_play.is_visible(timeout=500):
                return True

            # Canvas is active, not scopely blue backdrop, and not welcome aboard
            return not self._check_scopely_blue()
        except Exception:
            return False

    def wait_for_direct_play_button(self, timeout_ms: int = 60_000) -> bool:
        """Waits until the direct PLAY button (in-game lobby or portal) is rendered."""
        logger.info("Waiting for direct PLAY button on WebGL game portal (timeout=%dms)...", timeout_ms)
        try:
            poll_condition(
                lambda: True if self.is_direct_play_button_displayed() else None,
                timeout_ms=timeout_ms,
                interval_ms=500,
            )
            logger.info("Direct PLAY button detected on WebGL portal")
            return True
        except TimeoutError:
            raise TimeoutError(f"Direct PLAY button did not appear within {timeout_ms}ms on WebGL canvas") from None

    def click_direct_play(self, wait_after_click_sec: float = 0.0) -> WebGLGamePage:
        """Clicks the direct PLAY button on the WebGL canvas (or DOM overlay)."""
        logger.info("Clicking direct PLAY button on WebGL game portal")
        self.dismiss_cookie_banner()
        box = self.get_canvas_bounding_box()
        if box:
            # Bottom-right direct PLAY button in lobby (relative: ~0.87, ~0.87)
            self.game_canvas.click(
                position={"x": box["width"] * 0.87, "y": box["height"] * 0.87},
                delay=100,
            )
        else:
            vp = self.page.viewport_size or {"width": 1280, "height": 720}
            self.page.mouse.click(vp["width"] * 0.87, vp["height"] * 0.87)

        if wait_after_click_sec > 0:
            self.wait_seconds(wait_after_click_sec)

        return self

    def click_start_playing(self, wait_after_click_sec: float = 0.0) -> WebGLGamePage:
        """Clicks the 'START PLAYING!' button on the in-game Welcome Aboard dialog."""
        logger.info("Clicking 'START PLAYING!' button on WebGL canvas")
        self.dismiss_cookie_banner()
        box = self.get_canvas_bounding_box()
        if box:
            self.game_canvas.click(
                position={"x": box["width"] * 0.50, "y": box["height"] * 0.51},
                delay=100,
            )
        else:
            vp = self.page.viewport_size or {"width": 1280, "height": 720}
            self.page.mouse.click(vp["width"] * 0.484, vp["height"] * 0.514)

        if wait_after_click_sec > 0:
            logger.info("Waiting %.1f seconds after clicking START PLAYING", wait_after_click_sec)
            self.wait_seconds(wait_after_click_sec)

        return self

    def set_age_and_accept(self, age: int = 25) -> WebGLGamePage:
        """Sets the player age to the specified value (default 25) and accepts the age verification dialog."""
        logger.info("Setting player age to %d and accepting age verification", age)
        self.dismiss_cookie_banner()

        # 1. Check if HTML DOM age input/modal exists on current page or any popup window
        pages_to_check = [self.page] + [p for p in self.page.context.pages if p != self.page]
        for p in pages_to_check:
            try:
                dom_age_input = p.locator(
                    "input[type='number'], input[placeholder*='age' i], input[name*='age' i], [data-testid*='age' i]"
                ).first
                if dom_age_input.is_visible(timeout=1500):
                    logger.info("DOM age input detected on page (%s); entering age %d", p.url, age)
                    dom_age_input.fill(str(age))
                    dom_accept_button = p.locator(
                        "button:has-text('Accept'), button:has-text('Confirm'), "
                        "button:has-text('Continue'), button:has-text('OK')"
                    ).first
                    if dom_accept_button.is_visible(timeout=1000):
                        dom_accept_button.click()
                    return self
            except Exception:
                pass

        # 2. In-game WebGL Unity age gate interaction:
        box = self.get_canvas_bounding_box()
        if box:
            # Click center of the canvas where the age input / slider is mounted
            self.game_canvas.click(
                position={"x": box["width"] * 0.50, "y": box["height"] * 0.50},
                delay=100,
            )
            self.page.keyboard.type(str(age), delay=50)
            self.page.keyboard.press("Enter")

            # Click the Accept / Confirm button area (typically lower-middle of in-game dialog, ~62% down)
            self.wait_seconds(0.5)
            self.game_canvas.click(
                position={"x": box["width"] * 0.50, "y": box["height"] * 0.62},
                delay=100,
            )
        else:
            self.page.keyboard.type(str(age), delay=50)
            self.page.keyboard.press("Enter")

        return self

    def is_canvas_rendered(self) -> bool:
        """Evaluates whether the game canvas has non-zero dimensions and active layout."""
        box = self.get_canvas_bounding_box()
        return box is not None and box["width"] > 0 and box["height"] > 0

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
        box: FloatRect | None = self.game_canvas.bounding_box()
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
