from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

import pytest
from pydantic import BaseModel

from ui_test_platform.fixtures.api.plain_function import execute_api_request

if TYPE_CHECKING:
    from collections.abc import Callable

    from playwright.sync_api import APIRequestContext, Playwright

    from ui_test_platform.fixtures.api.types import ApiRequestParams

M = TypeVar("M", bound=BaseModel)


@pytest.fixture
def api_request(
    playwright: Playwright,
) -> Callable[[ApiRequestParams, type[M] | None], M | dict[str, object]]:
    """Fixture providing direct API request execution with pydantic schema validation."""
    request_context: APIRequestContext = playwright.request.new_context()

    def _call(
        params: ApiRequestParams,
        schema: type[M] | None = None,
    ) -> M | dict[str, object]:
        return execute_api_request(request_context, params, schema)

    return _call
