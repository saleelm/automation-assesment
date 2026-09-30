from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ui_test_platform.fixtures.pom.test_options import AppConfig, Tag, expect, step, tags, title
from ui_test_platform.test_data.shop.shop_data import ShopTestData

if TYPE_CHECKING:
    from ui_test_platform.pages.stumbleguys.shop_page import ShopPage

pytestmark = [pytest.mark.shop, pytest.mark.unauthenticated]


class TestShopPurchaseFlow:
    @tags(Tag.SMOKE, Tag.SHOP)
    @title("TC01 should display special deals catalog and validate player username")
    def test_tc01_should_display_special_deals_and_validate_username(self, shop_page: ShopPage) -> None:
        data = ShopTestData.generate()

        with step("Given the user navigates to the Stumble Guys Shop"):
            shop_page.navigate()

        with step("Then the Shop hero banner should be visible"):
            expect(shop_page.special_deals_header).to_be_visible(timeout=AppConfig.timeouts.navigate_expect)

        with step("When the user enters a valid player username"):
            shop_page.enter_username_and_validate(data.username)

        with step("Then the username input should retain the player identity"):
            expect(shop_page.username_input).to_have_value(data.username)

    @tags(Tag.E2E, Tag.SHOP, Tag.CHECKOUT)
    @title("TC02 should initiate purchase flow and safely cancel before payment confirmation")
    def test_tc02_should_safely_cancel_purchase_flow_before_confirmation(self, shop_page: ShopPage) -> None:
        data = ShopTestData.generate()

        with step("Given the user is on the Stumble Guys Shop with username validated"):
            shop_page.navigate()
            shop_page.enter_username_and_validate(data.username)

        with step("When the user selects an available offer"):
            # Verify catalog offer cards exist
            expect(shop_page.offer_cards.first).to_be_attached(timeout=AppConfig.timeouts.action)
            shop_page.select_first_available_offer()

        with step("Then the user safely cancels checkout before entering payment details"):
            shop_page.cancel_checkout_before_payment()

        with step("And the user remains on the shop portal with no purchase completed"):
            assert "/shop" in shop_page.page.url
