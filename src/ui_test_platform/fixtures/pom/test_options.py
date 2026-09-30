from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

import allure
from allure import step
from playwright.sync_api import Page, expect

from ui_test_platform.config.app_config import AppConfig
from ui_test_platform.enums.tags import Platform, Tag, tags

F = TypeVar("F", bound=Callable[..., Any])


def title(test_title: str) -> Callable[[F], F]:
    """Type-safe decorator wrapping allure.title."""
    return allure.title(test_title)  # type: ignore[no-any-return,no-untyped-call]


__all__ = ["AppConfig", "Page", "Platform", "Tag", "expect", "step", "tags", "title"]
