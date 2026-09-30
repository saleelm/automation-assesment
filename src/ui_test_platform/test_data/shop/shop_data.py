from __future__ import annotations

from dataclasses import dataclass

from ui_test_platform.helpers.random_data_helper import RandomDataHelper


@dataclass(frozen=True)
class ShopTestData:
    username: str
    invalid_username: str
    sample_offer_title: str

    @classmethod
    def generate(cls) -> ShopTestData:
        return cls(
            username=RandomDataHelper.random_username("LeadQA_"),
            invalid_username="",
            sample_offer_title="Special Deals",
        )
