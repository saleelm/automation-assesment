from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    client_id: str = Field(min_length=1)
    grant_type: str = Field(default="password")
    scope: str | None = Field(default=None)


class TokenResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    refresh_token: str | None = None
