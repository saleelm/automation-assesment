from __future__ import annotations

from typing import TYPE_CHECKING

from playwright.sync_api import expect

from ui_test_platform.config.app_config import AppConfig
from ui_test_platform.enums.tags import Platform
from ui_test_platform.pages.base_page import BasePage

if TYPE_CHECKING:
    from playwright.sync_api import Locator, Page


class ShopPage(BasePage):
    """Page Object for Stumble Guys Web Shop and Safe Purchase Flow."""

    def __init__(self, page: Page, platform: Platform = Platform.WEB) -> None:
        super().__init__(page, platform)

    @property
    def username_input(self) -> Locator:
        return self.page.locator("input[placeholder*='username' i]").first

    @property
    def validate_button(self) -> Locator:
        return self.page.locator("button:has-text('Validate'), button[type='submit']").first

    @property
    def special_deals_header(self) -> Locator:
        return self.page.locator("h1:has-text('SPECIAL DEALS ARE LIVE!'), h2:has-text('Special Deals')").first

    @property
    def offer_cards(self) -> Locator:
        return self.page.locator("div[role='status'], div[class*='grid'] > div, div:has(img[alt*='offer' i])")

    @property
    def first_purchasable_offer(self) -> Locator:
        return self.page.locator(
            "button:has-text('Buy'), button:has-text('$'), button:has-text('€'), "
            "button:has-text('Purchase'), div[class*='grid'] > div"
        ).first

    @property
    def checkout_modal(self) -> Locator:
        return self.page.locator(
            "[role='dialog'], iframe[src*='checkout'], iframe[src*='xsolla'], "
            "div[class*='modal'], div[class*='Checkout']"
        ).first

    @property
    def modal_close_button(self) -> Locator:
        return self.page.locator(
            "button[aria-label='Close'], button:has-text('✕'), button:has-text('×'), "
            "button:has-text('Cancel'), button[class*='close']"
        ).first

    def navigate(self) -> ShopPage:
        """Navigates to the Shop page and waits for shop anchors."""
        self.goto("/shop")
        self.expect_visible(self.special_deals_header, timeout=AppConfig.timeouts.navigate_expect)
        return self

    def enter_username_and_validate(self, username: str) -> None:
        """Enters player username and submits validation."""
        self.username_input.fill(username)
        # Verify validate button becomes active
        expect(self.validate_button).to_be_enabled(timeout=AppConfig.timeouts.action)
        self.validate_button.click()

    def select_first_available_offer(self) -> None:
        """Selects the first available shop offer to initiate checkout."""
        offer = self.first_purchasable_offer
        self.expect_visible(offer, timeout=AppConfig.timeouts.action)
        offer.click()

    def cancel_checkout_before_payment(self) -> None:
        """Safely dismisses or closes the checkout dialog without completing payment."""
        if self.modal_close_button.is_visible(timeout=3000):
            self.modal_close_button.click()
        else:
            # Press Escape key to safely dismiss modal
            self.page.keyboard.press("Escape")
