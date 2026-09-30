from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from typing import TypeVar

import pytest

F = TypeVar("F", bound=Callable[..., object])


class Platform(StrEnum):
    WEB = "web"
    MOBILE_EMULATED = "mobile-emulated"
    ANDROID_DEVICE = "android-device"

    @property
    def is_mobile(self) -> bool:
        return self in (Platform.MOBILE_EMULATED, Platform.ANDROID_DEVICE)


class Tag(StrEnum):
    AUTH = "auth"
    SMOKE = "smoke"
    SANITY = "sanity"
    REGRESSION = "regression"
    API = "api"
    E2E = "e2e"
    DESTRUCTIVE = "destructive"
    LOGIN = "login"
    ONBOARDING = "onboarding"
    PR_SANITY = "pr_sanity"
    SETUP = "setup"
    UNAUTHENTICATED = "unauthenticated"
    INTERSTITIAL_GATE = "interstitial_gate"
    WEB_ONLY = "web_only"
    MOBILE_ONLY = "mobile_only"
    SHOP = "shop"
    CHECKOUT = "checkout"
    GAME = "game"
    WEBGL = "webgl"


def tags(*tag_items: Tag) -> Callable[[F], F]:
    """Decorator to apply multiple Tag enum values as pytest markers."""

    def decorator(fn: F) -> F:
        for tag in reversed(tag_items):
            fn = pytest.mark.__getattr__(tag.value)(fn)
        return fn

    return decorator
