from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

logger = logging.getLogger("ui_test_platform.helpers.user_credential_store")

_STORE_PATH = Path("playwright/.auth/test_user.json")
DEFAULT_TEST_USER_EMAIL = "stumble_qa_173996@maxxspace.com"


class TestUser(TypedDict, total=False):
    """Persisted test user credentials used across test runs."""

    email: str
    mail_token: str
    created_at: str
    verified: bool
    username: str


def load_test_user() -> TestUser | None:
    """Returns the persisted TestUser if the store file exists and is verified.

    Returns None if the file is missing, corrupt, or the account is not yet verified.
    If the store file is missing, automatically initializes the default signed-up user.
    """
    if not _STORE_PATH.exists() or _STORE_PATH.stat().st_size == 0:
        logger.debug(
            "No persisted test user found at %s — initializing default signed-up account %s",
            _STORE_PATH,
            DEFAULT_TEST_USER_EMAIL,
        )
        try:
            from ui_test_platform.helpers.email_otp_helper import TempMailClient

            client = TempMailClient()
            token = client.get_token_for_address(DEFAULT_TEST_USER_EMAIL)
            save_test_user(
                email=DEFAULT_TEST_USER_EMAIL,
                mail_token=token,
                verified=True,
                username="stumble_qa_173996",
            )
        except Exception as exc:
            logger.warning("Could not auto-initialize default test user (%s)", exc)
            return None

    try:
        raw = json.loads(_STORE_PATH.read_text(encoding="utf-8"))
        user: TestUser = {
            "email": str(raw["email"]),
            "mail_token": str(raw["mail_token"]),
            "created_at": str(raw["created_at"]),
            "verified": bool(raw["verified"]),
        }
        if raw.get("username"):
            user["username"] = str(raw["username"])
        if not user["verified"]:
            logger.info("Persisted test user exists but is not yet verified — will re-run full signup")
            return None
        logger.info("Loaded persisted test user: %s (created %s)", user["email"], user["created_at"])
        return user
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        logger.warning("test_user.json is corrupt or incomplete (%s) — will re-run full signup", exc)
        return None


def save_test_user(
    email: str,
    mail_token: str,
    *,
    verified: bool,
    username: str | None = None,
) -> None:
    """Persists test user credentials to playwright/.auth/test_user.json.

    Args:
        email: The disposable email address used to create the account.
        mail_token: The Mail.tm JWT token for reading the inbox.
        verified: Whether email verification has been completed.
        username: Optional in-game player username.
    """
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    user: TestUser = {
        "email": email,
        "mail_token": mail_token,
        "created_at": datetime.now(tz=UTC).isoformat(),
        "verified": verified,
    }
    if username:
        user["username"] = username
    _STORE_PATH.write_text(json.dumps(user, indent=2), encoding="utf-8")
    logger.info(
        "Persisted test user to %s → email=%s verified=%s username=%s",
        _STORE_PATH,
        email,
        verified,
        username,
    )


def update_test_username(username: str) -> None:
    """Updates or sets the in-game player username for the persisted test user."""
    user = load_test_user()
    if user:
        save_test_user(
            email=user["email"],
            mail_token=user["mail_token"],
            verified=user.get("verified", True),
            username=username,
        )


def clear_test_user() -> None:
    """Removes the persisted test user file, forcing a full re-signup on next run."""
    if _STORE_PATH.exists():
        _STORE_PATH.unlink()
        logger.info("Cleared persisted test user at %s", _STORE_PATH)
