from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page


class MobileHelper:
    """Mobile gesture and viewport utilities for Chromium/Android touch contexts."""

    @staticmethod
    def swipe_up(page: Page, distance_px: int = 400) -> None:
        """Simulates an upward swipe gesture using touch mouse dispatch."""
        viewport = page.viewport_size or {"width": 390, "height": 844}
        start_x = viewport["width"] // 2
        start_y = int(viewport["height"] * 0.75)
        end_y = max(10, start_y - distance_px)

        page.mouse.move(start_x, start_y)
        page.mouse.down()
        page.mouse.move(start_x, end_y, steps=10)
        page.mouse.up()

    @staticmethod
    def swipe_down(page: Page, distance_px: int = 400) -> None:
        """Simulates a downward swipe gesture using touch mouse dispatch."""
        viewport = page.viewport_size or {"width": 390, "height": 844}
        start_x = viewport["width"] // 2
        start_y = int(viewport["height"] * 0.25)
        end_y = min(viewport["height"] - 10, start_y + distance_px)

        page.mouse.move(start_x, start_y)
        page.mouse.down()
        page.mouse.move(start_x, end_y, steps=10)
        page.mouse.up()

    @staticmethod
    def scroll_into_view_center(page: Page, selector: str) -> None:
        """Evaluates element bounding box and scrolls it directly into center view."""
        page.locator(selector).first.scroll_into_view_if_needed()
