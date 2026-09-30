from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar, cast

from pydantic import BaseModel

from ui_test_platform.config.app_config import AppConfig

if TYPE_CHECKING:
    from playwright.sync_api import APIRequestContext

    from ui_test_platform.fixtures.api.types import ApiRequestParams

M = TypeVar("M", bound=BaseModel)


def execute_api_request(
    request: APIRequestContext,
    params: ApiRequestParams,
    schema: type[M] | None = None,
) -> M | dict[str, object]:
    """Executes a direct API call, verifies HTTP status, and validates response schema."""
    url = (
        params.path if params.path.startswith("http") else f"{AppConfig.api_url.rstrip('/')}/{params.path.lstrip('/')}"
    )

    kwargs: dict[str, object] = {
        "headers": params.headers,
        "params": params.query,
    }
    if params.data is not None:
        if isinstance(params.data, (dict, list)):
            kwargs["data"] = params.data
        else:
            kwargs["data"] = str(params.data)

    response = request.fetch(url, method=params.method, **kwargs)  # type: ignore[arg-type]

    if response.status != params.expected_status:
        msg = f"API request {params.method} {url} returned status {response.status}, expected {params.expected_status}."
        raise AssertionError(f"{msg} Body: {response.text()}")

    json_data: Any = response.json()
    if schema:
        return schema.model_validate(json_data)
    return cast("dict[str, object]", json_data)
