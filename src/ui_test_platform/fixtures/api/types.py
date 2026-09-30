from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ApiRequestParams(BaseModel):
    model_config = ConfigDict(frozen=True)

    method: str = Field(default="GET")
    path: str
    data: Any = Field(default=None)
    headers: dict[str, str] = Field(default_factory=dict)
    query: dict[str, str] = Field(default_factory=dict)
    expected_status: int = Field(default=200)
