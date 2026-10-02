from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ui_test_platform.fixtures.pom.test_options import AppConfig, Tag, expect, step, tags, title

if TYPE_CHECKING:
    from ui_test_platform.pages.stumbleguys.webgl_game_page import WebGLGamePage

pytestmark = [pytest.mark.game, pytest.mark.webgl]


class TestWebGLGamePortal:
    @tags(Tag.SMOKE, Tag.GAME, Tag.WEBGL, Tag.WEB_ONLY)
    @title("TC01 should initialize WebGL game container and support canvas context")
    def test_tc01_should_initialize_webgl_game_container(self, game_page: WebGLGamePage) -> None:
        with step("Given the user navigates to the Stumble Guys WebGL portal"):
            game_page.navigate()

        with step("Then the game player container should be mounted"):
            expect(game_page.player_container).to_be_visible(timeout=AppConfig.timeouts.navigate_expect)

        with step("And the browser runtime should support WebGL2/WebGL context"):
            assert game_page.is_webgl_supported() is True, "WebGL is not supported in the current browser"

    @tags(Tag.E2E, Tag.GAME, Tag.WEBGL, Tag.WEB_ONLY)
    @title("TC02 should dispatch canvas viewport click and keyboard controls")
    def test_tc02_should_dispatch_canvas_viewport_interactions(self, game_page: WebGLGamePage) -> None:
        with step("Given the WebGL game portal is loaded"):
            game_page.navigate()

        with step("When the user clicks the center of the WebGL canvas"):
            game_page.dispatch_canvas_click(relative_x=0.5, relative_y=0.5)

        with step("And dispatches gameplay navigation keys (Space, Arrow keys)"):
            game_page.dispatch_gameplay_keys(["Space", "ArrowRight", "ArrowLeft"])

        with step("Then the game container should remain active and responsive"):
            expect(game_page.player_container).to_be_visible()
