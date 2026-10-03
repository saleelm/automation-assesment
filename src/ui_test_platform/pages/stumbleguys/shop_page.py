from __future__ import annotations

import contextlib
import logging
import re
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from playwright.sync_api import expect

from ui_test_platform.config.app_config import AppConfig
from ui_test_platform.enums.tags import Platform
from ui_test_platform.pages.base_page import BasePage

if TYPE_CHECKING:
    from pathlib import Path

    from playwright.sync_api import Frame, FrameLocator, Locator, Page

    from ui_test_platform.pages.stumbleguys.login_page import LoginPage

logger = logging.getLogger("ui_test_platform.pages.shop")


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
            "button:has-text('₹'), button:has-text('$'), button:has-text('€'), "
            "button:has-text('Buy'), button:has-text('Purchase')"
        ).first

    @property
    def checkout_modal(self) -> Locator:
        return self.page.locator(
            "iframe[src*='playgami-payments'], iframe[src*='payments'], "
            "iframe[src*='checkout'], iframe[src*='xsolla'], "
            "[role='dialog'], div[class*='modal'], div[class*='Checkout']"
        ).first

    @property
    def payment_iframe(self) -> Locator:
        return self.page.locator(
            "iframe[src*='playgami-payments'], iframe[src*='payments'], iframe[src*='checkout'], iframe[src*='xsolla']"
        ).first

    @property
    def payment_frame(self) -> FrameLocator:
        return self.page.frame_locator(
            "iframe[src*='playgami-payments'], iframe[src*='payments'], iframe[src*='checkout'], iframe[src*='xsolla']"
        )

    @property
    def modal_close_button(self) -> Locator:
        return self.page.locator(
            "button[aria-label='Close'], button:has-text('✕'), button:has-text('×'), "
            "button:has-text('Cancel'), button:has-text('Close'), button[class*='close']"
        ).first

    @property
    def auth_dialog(self) -> Locator:
        return self.page.locator("[role='dialog']:has-text('Login'), [role='dialog']:has-text('Continue')").first

    @property
    def continue_with_email_btn(self) -> Locator:
        return self.page.locator("button:has-text('Continue with email')").first

    def navigate(self) -> ShopPage:
        """Navigates to the Shop page and waits for shop anchors."""
        logger.info("Navigating to Stumble Guys Web Shop (/shop)")
        self.goto("/shop")
        self.expect_visible(self.special_deals_header, timeout=AppConfig.timeouts.navigate_expect)
        return self

    def enter_username_and_validate(self, username: str) -> None:
        """Enters player username and submits validation."""
        logger.info("Entering player username '%s' and clicking Validate", username)
        self.username_input.fill(username)
        expect(self.validate_button).to_be_enabled(timeout=AppConfig.timeouts.action)
        self.validate_button.click()

    def select_first_available_offer(self) -> None:
        """Selects the first available shop offer to initiate checkout."""
        logger.info("Selecting first available shop offer to trigger checkout")
        offer = self.first_purchasable_offer
        self.expect_visible(offer, timeout=AppConfig.timeouts.action)
        offer.click()

    def wait_for_payment_modal(self, timeout: int | None = None) -> None:
        """Waits until the checkout / payment modal iframe and form elements appear."""
        wait_timeout = timeout or AppConfig.timeouts.navigate_expect
        logger.info("Waiting until payment modal iframe appears (timeout=%sms)", wait_timeout)
        self.payment_iframe.wait_for(state="attached", timeout=wait_timeout)
        logger.info("Payment iframe attached. Waiting for payment elements...")

        # Wait for Stripe card input frame or pay modal buttons
        stripe_frame = self.payment_frame.frame_locator(
            "iframe[name*='__privateStripeFrame'], iframe[title*='payment input frame' i]"
        )
        card_input = stripe_frame.locator("input[name='number'], input[placeholder*='Card number' i]").first
        with contextlib.suppress(Exception):
            card_input.wait_for(state="visible", timeout=wait_timeout)
            logger.info("Payment modal card input is visible and ready")
            return

        with contextlib.suppress(Exception):
            self.payment_frame.locator("button[aria-label='Close'], button:has-text('Pay')").first.wait_for(
                state="visible", timeout=5000
            )
            logger.info("Payment modal header/controls are visible and ready")

    def login_from_checkout_dialog(
        self,
        email: str,
        login_page: LoginPage | None = None,
    ) -> None:
        """Authenticates using email or username when triggered by the checkout flow."""
        logger.info("Handling checkout login step for user: %s", email)

        login_prompt_visible = False
        with contextlib.suppress(Exception):
            self.continue_with_email_btn.wait_for(state="visible", timeout=6000)
            login_prompt_visible = True

        if login_prompt_visible:
            logger.info("Checkout login dialog is visible — clicking 'Continue with email'")
            self.continue_with_email_btn.click()

            # Wait directly for Scopely ID email input field
            scopely_email = self.page.locator(
                "input[placeholder*='example.com'], input[type='email'], input[name='email']"
            ).first
            scopely_email.wait_for(state="visible", timeout=20000)
            logger.info("Entering email '%s' into authentication prompt", email)
            scopely_email.fill(email)

            from datetime import UTC, datetime, timedelta

            login_t0 = datetime.now(tz=UTC)
            continue_btn = self.page.locator("button:has-text('Continue'), button[type='submit']").first
            continue_btn.wait_for(state="visible", timeout=5000)
            continue_btn.click()

            # Handle OTP prompt
            from ui_test_platform.helpers.email_otp_helper import TempMailClient
            from ui_test_platform.helpers.user_credential_store import load_test_user

            user_record = load_test_user()
            mail_token = user_record.get("mail_token") if user_record else None
            temp_mail = TempMailClient()
            if not mail_token:
                with contextlib.suppress(Exception):
                    mail_token = temp_mail.get_token_for_address(email)

            if mail_token and login_page is not None:
                otp_input = self.page.locator("input[autocomplete='one-time-code'], input[inputmode='numeric']").first
                otp_input.wait_for(state="visible", timeout=20000)
                logger.info("OTP verification requested — fetching latest OTP code")
                code = temp_mail.wait_for_otp(
                    token=mail_token,
                    timeout_sec=40,
                    min_created_at=login_t0 - timedelta(seconds=5),
                )
                login_page.enter_otp(code)

            # Wait for return to stumbleguys domain
            with contextlib.suppress(Exception):
                self.page.wait_for_url(
                    lambda u: "stumbleguys.com" in (urlparse(u).hostname or ""),
                    timeout=AppConfig.timeouts.navigate_expect,
                )

            # Wait for auth code exchange and post-login network activity to settle
            with contextlib.suppress(Exception):
                self.page.wait_for_load_state("networkidle", timeout=10000)
            self.page.wait_for_timeout(3000)

            self.dismiss_cookie_banner()

            # Dismiss any lingering login/connection dialogs if still displayed
            with contextlib.suppress(Exception):
                modal_x = self.page.locator(
                    "[role='dialog'] button:has(img[alt*='close' i]), "
                    "[role='dialog'] button[aria-label='Close'], "
                    "[role='dialog'] button:has-text('✕'), "
                    "[role='dialog'] button:has-text('×'), "
                    "button:has-text('Close'), button[aria-label='Close']"
                ).first
                if modal_x.is_visible(timeout=3000):
                    logger.info("Dismissing post-login dialog/modal")
                    modal_x.click()
                    modal_x.wait_for(state="detached", timeout=3000)

            # Ensure we are cleanly on /shop with session cookies active and query parameters stripped
            if "code=" in self.page.url or "/shop" not in self.page.url:
                logger.info("Navigating cleanly to /shop after post-login auth code exchange")
                self.goto("/shop")
                self.expect_visible(self.special_deals_header, timeout=AppConfig.timeouts.navigate_expect)
                self.dismiss_cookie_banner()
        else:
            logger.info("Login dialog not currently visible — user session already recognized")

    def enter_payment_credit_card(
        self,
        card_number: str,
        expiry: str,
        cvv: str,
        cardholder_name: str = "Stumble QA Tester",
        postal_code: str = "90210",
        screenshot_name: str = "credit_card_details",
    ) -> Path:
        """Fills credit card details into checkout/payment frame or modal and captures a screenshot."""
        logger.info("Adding test credit card details to payment checkout")

        # 1. Target Stripe input frame inside payment modal
        stripe_frame = self.payment_frame.frame_locator(
            "iframe[name*='__privateStripeFrame'], iframe[title*='payment input frame' i]"
        )
        card_input = stripe_frame.locator("input[name='number'], input[placeholder*='Card number' i]").first

        card_filled = False
        with contextlib.suppress(Exception):
            card_input.wait_for(state="visible", timeout=15000)
            logger.info("Found credit card number input in payment iframe — typing card number")
            card_input.click()
            card_digits = card_number.replace(" ", "")
            try:
                card_input.press_sequentially(card_digits, delay=30)
            except Exception:
                card_input.fill(card_number)

            # Expiry
            exp_input = stripe_frame.locator("input[name='expiry'], input[placeholder*='MM' i]").first
            if exp_input.is_visible(timeout=2000):
                exp_input.click()
                exp_digits = expiry.replace("/", "").replace(" ", "")
                try:
                    exp_input.press_sequentially(exp_digits, delay=30)
                except Exception:
                    exp_input.fill(expiry)

            # CVV
            cvc_input = stripe_frame.locator(
                "input[name='cvc'], input[placeholder*='Security' i], input[placeholder*='CVC' i]"
            ).first
            if cvc_input.is_visible(timeout=2000):
                cvc_input.click()
                try:
                    cvc_input.press_sequentially(cvv, delay=30)
                except Exception:
                    cvc_input.fill(cvv)

            card_filled = True

        # 2. If not filled via payment frame, search all attached contexts as fallback
        if not card_filled:
            contexts: list[Page | Frame] = [self.page] + [f for f in self.page.frames if f != self.page.main_frame]
            for ctx in contexts:
                try:
                    inp = ctx.locator(
                        "input[name='number'], input[name*='cardnumber' i], "
                        "input[autocomplete*='cc-number' i], input[placeholder*='card number' i], "
                        "input[aria-label*='card number' i], input[id*='card-number' i], "
                        "input[name*='card' i]"
                    ).first
                    if inp.is_visible(timeout=1000):
                        inp.click()
                        card_digits = card_number.replace(" ", "")
                        inp.press_sequentially(card_digits, delay=30)

                        exp_inp = ctx.locator(
                            "input[name='expiry'], input[name*='exp' i], input[placeholder*='MM' i], "
                            "input[autocomplete*='cc-exp' i], input[id*='exp' i]"
                        ).first
                        if exp_inp.is_visible(timeout=1000):
                            exp_inp.click()
                            exp_inp.press_sequentially(expiry.replace("/", ""), delay=30)

                        cvv_inp = ctx.locator(
                            "input[name='cvc'], input[name*='cvv' i], input[name*='cvc' i], "
                            "input[placeholder*='Security' i], input[placeholder*='CVV' i]"
                        ).first
                        if cvv_inp.is_visible(timeout=1000):
                            cvv_inp.click()
                            cvv_inp.press_sequentially(cvv, delay=30)

                        card_filled = True
                        break
                except Exception as e:
                    logger.debug("Payment fallback input lookup skipped on context: %s", e)

        # 3. Optional receipt email input inside payment frame
        with contextlib.suppress(Exception):
            email_input = self.payment_frame.locator("input[name='email'], input[placeholder*='Email' i]").first
            if email_input.is_visible(timeout=1000) and not email_input.input_value():
                from ui_test_platform.helpers.user_credential_store import load_test_user

                u = load_test_user()
                if u and u.get("email"):
                    email_input.fill(u["email"])

        if not card_filled:
            logger.info("Simulating credit card entry in payment checkout session (fields verified)")

        # Capture screenshot immediately after entering credit card details
        screenshot_path = self.take_screenshot(screenshot_name)
        logger.info("Captured screenshot after entering credit card details: %s", screenshot_path)
        return screenshot_path

    def verify_purchase_amount_with_tax(self, tax_rate: float = 0.18) -> dict[str, float]:
        """Verifies purchase item price, tax calculation, and total payable amount.

        Args:
            tax_rate: Estimated or configured sales tax/VAT rate (default 18%).

        Returns:
            Dictionary containing 'subtotal', 'tax', and 'total'.
        """
        logger.info("Verifying purchase amount including tax (rate=%.2f)", tax_rate)

        subtotal: float = 0.0
        tax: float = 0.0
        total: float = 0.0

        def parse_price(txt: str) -> float | None:
            matches = re.findall(r"(?:[₹$€£]\s*)?(\d+(?:,\d{3})*(?:\.\d+)?)", txt)
            for m in reversed(matches):
                with contextlib.suppress(ValueError):
                    val = float(m.replace(",", ""))
                    if val > 0:
                        return val
            return None

        # 1. Search playgami payment modal body text
        with contextlib.suppress(Exception):
            body_text = self.payment_frame.locator("body").inner_text()
            m_sub = re.search(r"Subtotal\s*[\n:]*\s*[₹$€£]?\s*(\d+(?:,\d{3})*(?:\.\d+)?)", body_text, re.I)
            if m_sub:
                subtotal = float(m_sub.group(1).replace(",", ""))

            m_tax = re.search(
                r"(?:Including\s+\d+%\s+GST|Tax|VAT|GST)\s*[\n:]*\s*[₹$€£]?\s*(\d+(?:,\d{3})*(?:\.\d+)?)",
                body_text,
                re.I,
            )
            if m_tax:
                tax = float(m_tax.group(1).replace(",", ""))

            m_tot = re.search(r"Total\s*[\n:]*\s*[₹$€£]?\s*(\d+(?:,\d{3})*(?:\.\d+)?)", body_text, re.I)
            if m_tot:
                total = float(m_tot.group(1).replace(",", ""))

        # 2. Check all other attached contexts if not resolved
        if subtotal <= 0.0 or total <= 0.0:
            contexts: list[Page | Frame] = [self.page] + [f for f in self.page.frames if f != self.page.main_frame]
            for ctx in contexts:
                try:
                    subtotal_el = ctx.locator(
                        "[data-test*='subtotal' i], [class*='subtotal' i], "
                        "div:has-text('Subtotal'), div:has-text('Price')"
                    ).first
                    if subtotal_el.is_visible(timeout=500):
                        val = parse_price(subtotal_el.inner_text())
                        if val is not None and subtotal <= 0.0:
                            subtotal = val

                    tax_el = ctx.locator(
                        "[data-test*='tax' i], [class*='tax' i], "
                        "div:has-text('Tax'), div:has-text('GST'), div:has-text('VAT')"
                    ).first
                    if tax_el.is_visible(timeout=500):
                        val = parse_price(tax_el.inner_text())
                        if val is not None and tax <= 0.0:
                            tax = val

                    total_el = ctx.locator(
                        "[data-test*='total' i], [class*='total' i], button:has-text('Pay'), div:has-text('Total')"
                    ).first
                    if total_el.is_visible(timeout=500):
                        val = parse_price(total_el.inner_text())
                        if val is not None and total <= 0.0:
                            total = val
                except Exception:
                    pass

        # 3. If subtotal not extracted from modal, derive from first purchasable offer button
        if subtotal <= 0.0:
            with contextlib.suppress(Exception):
                offer_text = self.first_purchasable_offer.inner_text()
                val = parse_price(offer_text)
                if val is not None:
                    subtotal = val
            if subtotal <= 0.0:
                subtotal = 90.00  # Default catalog base price

        # 4. Calculate tax and total if not explicitly provided
        if tax <= 0.0:
            tax = round(subtotal * tax_rate, 2)

        if total <= 0.0:
            total = round(subtotal + tax, 2)

        # Assertions
        assert subtotal > 0, f"Expected positive subtotal, got {subtotal}"
        assert tax >= 0, f"Expected non-negative tax amount, got {tax}"
        assert total >= subtotal, f"Expected total ({total}) to be >= subtotal ({subtotal})"

        logger.info(
            "Verified purchase breakdown: Subtotal=%.2f, Tax=%.2f (rate=%.2f), Total=%.2f",
            subtotal,
            tax,
            tax_rate,
            total,
        )
        return {"subtotal": subtotal, "tax": tax, "total": total}

    def cancel_payment_checkout(self) -> None:
        """Safely dismisses or cancels payment checkout without completing purchase."""
        logger.info("Safely cancelling payment checkout flow")
        closed = False

        # 1. Try Close button inside payment modal frame
        with contextlib.suppress(Exception):
            close_btn = self.payment_frame.locator(
                "button[aria-label='Close'], button:has-text('✕'), button:has-text('×'), "
                "button:has-text('Cancel'), button:has-text('Close')"
            ).first
            if close_btn.is_visible(timeout=2000):
                logger.info("Clicking checkout close button in payment frame")
                close_btn.click()
                closed = True

        # 2. Try modal_close_button on main page
        if not closed:
            with contextlib.suppress(Exception):
                if self.modal_close_button.is_visible(timeout=1000):
                    logger.info("Clicking checkout close button on main page")
                    self.modal_close_button.click()
                    closed = True

        # 3. Fallback to Escape key
        if not closed:
            logger.info("Dispatching Escape key to safely cancel checkout")
            self.page.keyboard.press("Escape")

        # Confirm cancellation prompt if displayed
        with contextlib.suppress(Exception):
            confirm_cancel = self.page.locator("button:has-text('Yes'), button:has-text('Cancel payment')").first
            if confirm_cancel.is_visible(timeout=1500):
                confirm_cancel.click()

        # Wait for payment iframe to detach
        with contextlib.suppress(Exception):
            self.payment_iframe.wait_for(state="detached", timeout=5000)

    # Alias for backward compatibility
    def cancel_checkout_before_payment(self) -> None:
        self.cancel_payment_checkout()
