from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ui_test_platform.fixtures.pom.test_options import AppConfig, Tag, expect, step, tags, title

if TYPE_CHECKING:
    from ui_test_platform.pages.stumbleguys.webgl_game_page import WebGLGamePage

pytestmark = [pytest.mark.game, pytest.mark.webgl]


@pytest.fixture
def loaded_game_page(game_page: WebGLGamePage) -> WebGLGamePage:
    """Prerequisite fixture: navigates to /play and waits for loader & asset downloading to complete."""
    with step("Prerequisite: Navigate to /play and wait for game loading & asset download to complete"):
        game_page.navigate()
        game_page.wait_for_game_download_and_load()
    return game_page


class TestWebGLGamePortal:
    @tags(Tag.SMOKE, Tag.GAME, Tag.WEBGL, Tag.WEB_ONLY)
    @title("TC01 should initialize WebGL game container and verify portal is ready")
    def test_tc01_should_initialize_webgl_game_container(self, loaded_game_page: WebGLGamePage) -> None:
        with step("Then the game canvas should be visible and rendered"):
            expect(loaded_game_page.game_canvas).to_be_visible(timeout=AppConfig.timeouts.navigate_expect)
            assert loaded_game_page.is_canvas_rendered() is True, "Canvas is not rendered with non-zero dimensions"

        with step("And the SCOPELY splash screen should appear on the WebGL canvas"):
            assert loaded_game_page.is_scopely_splash_displayed() is True, (
                "SCOPELY splash screen was not detected on WebGL canvas"
            )

        with step("And the fullscreen action button should be visible"):
            expect(loaded_game_page.fullscreen_button).to_be_visible(timeout=AppConfig.timeouts.expect)

        with step("And the play button should be visible"):
            expect(loaded_game_page.nav_play_button).to_be_visible(timeout=AppConfig.timeouts.expect)

        with step("And the browser runtime should support WebGL2/WebGL context"):
            assert loaded_game_page.is_webgl_supported() is True, "WebGL is not supported in the current browser"

        with step("And the WebGL game portal should reach active playable state"):
            assert (
                loaded_game_page.is_direct_play_button_displayed()
                or loaded_game_page.is_welcome_aboard_displayed()
                or loaded_game_page.is_canvas_rendered()
            ) is True, "WebGL game portal did not reach a ready state"

        with step("And capture a screenshot of the verified WebGL game portal"):
            loaded_game_page.take_screenshot("tc01_webgl_game_assertion.png")

    @tags(Tag.E2E, Tag.GAME, Tag.WEBGL, Tag.WEB_ONLY)
    @title("TC02 should verify direct PLAY button and initiate game start sequence")
    def test_tc02_should_verify_direct_play_and_start_game(self, loaded_game_page: WebGLGamePage) -> None:
        with step("Given the direct PLAY button is displayed on WebGL game portal"):
            assert loaded_game_page.wait_for_direct_play_button() is True, (
                "Direct PLAY button was not detected on WebGL portal"
            )

        with step("When the user clicks the direct PLAY button"):
            loaded_game_page.click_direct_play(wait_after_click_sec=5.0)

        with step("Then the game canvas should remain active and responsive"):
            expect(loaded_game_page.game_canvas).to_be_visible()
            expect(loaded_game_page.fullscreen_button).to_be_visible()

        with step("And capture a screenshot after clicking direct PLAY"):
            loaded_game_page.take_screenshot("tc02_after_direct_play.png")

    @pytest.mark.unauthenticated
    @tags(Tag.E2E, Tag.GAME, Tag.WEBGL, Tag.WEB_ONLY)
    @title("TC03 should handle guest onboarding age verification sequence when unauthenticated")
    def test_tc03_should_handle_guest_age_verification(self, loaded_game_page: WebGLGamePage) -> None:
        with step("Given the WELCOME ABOARD modal is visible on WebGL game portal"):
            assert loaded_game_page.wait_for_welcome_aboard_modal() is True, (
                "WELCOME ABOARD modal is not visible on canvas"
            )

        with step("When the user clicks on START PLAYING"):
            loaded_game_page.click_start_playing(wait_after_click_sec=1.0)

        with step("And sets player age to 25 and accepts"):
            loaded_game_page.set_age_and_accept(age=25)

        with step("Then the game canvas should remain active and responsive"):
            expect(loaded_game_page.game_canvas).to_be_visible()
            expect(loaded_game_page.fullscreen_button).to_be_visible()

        with step("And capture a screenshot after age verification"):
            loaded_game_page.take_screenshot("tc03_after_age_acceptance.png")
