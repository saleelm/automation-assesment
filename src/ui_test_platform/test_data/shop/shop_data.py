from __future__ import annotations

from dataclasses import dataclass

from ui_test_platform.config.app_config import AppConfig
from ui_test_platform.helpers.random_data_helper import RandomDataHelper
from ui_test_platform.helpers.user_credential_store import load_test_user


@dataclass(frozen=True)
class ShopTestData:
    username: str
    email: str
    invalid_username: str
    sample_offer_title: str
    card_number: str
    card_expiry: str
    card_cvv: str
    cardholder_name: str
    postal_code: str
    tax_rate: float

    @classmethod
    def generate(cls) -> ShopTestData:
        test_user = load_test_user()
        try:
            cfg_email = AppConfig.credentials.email
        except Exception:
            cfg_email = "stumble_qa_173996@maxxspace.com"

        email = test_user["email"] if test_user else cfg_email
        username = (
            str(test_user["username"])
            if (test_user and test_user.get("username"))
            else RandomDataHelper.random_username("LeadQA_")
        )

        return cls(
            username=username,
            email=email,
            invalid_username="",
            sample_offer_title="Special Deals",
            card_number="4242 4242 4242 4242",
            card_expiry="12/28",
            card_cvv="123",
            cardholder_name="Stumble QA Tester",
            postal_code="90210",
            tax_rate=0.18,
        )
