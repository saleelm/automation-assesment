from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ui_test_platform.fixtures.pom.test_options import AppConfig, Tag, expect, step, tags, title
from ui_test_platform.test_data.shop.shop_data import ShopTestData

if TYPE_CHECKING:
    from ui_test_platform.pages.stumbleguys.login_page import LoginPage
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
    @title("TC02 should initiate purchase flow, login, add card details, verify tax amount, and cancel")
    def test_tc02_should_safely_cancel_purchase_flow_before_confirmation(
        self, shop_page: ShopPage, login_page: LoginPage
    ) -> None:
        data = ShopTestData.generate()

        with step("Given the user is on the Stumble Guys Shop with username validated"):
            shop_page.navigate()
            shop_page.enter_username_and_validate(data.username)

        with step("When the user selects an available offer"):
            # Verify catalog offer cards exist
            expect(shop_page.offer_cards.first).to_be_attached(timeout=AppConfig.timeouts.action)
            shop_page.select_first_available_offer()

        with step("And the user logs in with their username or email to proceed to checkout"):
            shop_page.login_from_checkout_dialog(
                email=data.email,
                login_page=login_page,
            )

        with step("When the user selects the offer again after logging in"):
            shop_page.select_first_available_offer()

        with step("And waits until the payment modal appears"):
            shop_page.wait_for_payment_modal()

        with step("And enters credit card details and captures screenshot"):
            screenshot_path = shop_page.enter_payment_credit_card(
                card_number=data.card_number,
                expiry=data.card_expiry,
                cvv=data.card_cvv,
                cardholder_name=data.cardholder_name,
                postal_code=data.postal_code,
                screenshot_name="credit_card_details",
            )
            assert screenshot_path.exists(), f"Screenshot was not generated at {screenshot_path}"

        with step("Then the user verifies the purchase amount including tax"):
            breakdown = shop_page.verify_purchase_amount_with_tax(tax_rate=data.tax_rate)
            assert breakdown["total"] >= breakdown["subtotal"]
            assert breakdown["tax"] >= 0

        with step("When the user safely cancels the payment flow before confirmation"):
            shop_page.cancel_payment_checkout()

        with step("Then the user remains on the shop portal with no purchase completed"):
            assert "/shop" in shop_page.page.url
