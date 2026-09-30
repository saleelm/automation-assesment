from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Endpoint:
    method: str
    path: str
    pattern: str


@dataclass(frozen=True)
class AuthApiConstants:
    TOKEN: Endpoint = Endpoint(
        method="POST",
        path="/protocol/openid-connect/token",
        pattern=r"/protocol/openid-connect/token",
    )
    USER_INFO: Endpoint = Endpoint(
        method="GET",
        path="/protocol/openid-connect/userinfo",
        pattern=r"/protocol/openid-connect/userinfo",
    )
    SESSION_CHECK: Endpoint = Endpoint(
        method="GET",
        path="/v2/session/check",
        pattern=r"/v2/session/check",
    )
