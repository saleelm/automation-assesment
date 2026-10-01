from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, TypeVar

import allure
from playwright.sync_api import Page, expect

from ui_test_platform.config.app_config import AppConfig
from ui_test_platform.enums.tags import Platform, Tag, tags

F = TypeVar("F", bound=Callable[..., Any])
step_logger = logging.getLogger("ui_test_platform.step")


class StepLogger:
    """Wrapper around allure.step providing simultaneous logging and Allure report integration."""

    def __init__(self, title: str) -> None:
        self.title = title
        self._ctx = allure.step(title)

    def __enter__(self) -> Any:
        step_logger.info("👉 STEP: %s", self.title)
        return self._ctx.__enter__()  # type: ignore[no-untyped-call]

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> Any:
        return self._ctx.__exit__(exc_type, exc_val, exc_tb)  # type: ignore[no-untyped-call]

    def __call__(self, func: F) -> F:
        res: F = self._ctx(func)
        return res


def step(title: str) -> StepLogger:
    """Creates a step that emits an INFO log and reports to Allure."""
    return StepLogger(title)


def title(test_title: str) -> Callable[[F], F]:
    """Type-safe decorator wrapping allure.title."""
    return allure.title(test_title)  # type: ignore[no-any-return,no-untyped-call]


__all__ = ["AppConfig", "Page", "Platform", "Tag", "expect", "step", "tags", "title"]
