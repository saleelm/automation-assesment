from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ShopOfferItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int | str
    title: str
    sku_name: str
    price: float | str | None = None


class CheckoutSessionRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    sku_name: str = Field(min_length=1)
    username: str = Field(min_length=1)
    currency: str = Field(default="USD")
