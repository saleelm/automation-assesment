from __future__ import annotations

import json
import logging
import random
import re
import time
import urllib.request
from datetime import UTC, datetime
from urllib.error import HTTPError

logger = logging.getLogger("ui_test_platform.helpers.email_otp")


class MailServiceRateLimitError(Exception):
    """Raised when the public temp mail API rate limits requests (HTTP 429)."""


class TempMailClient:
    """Zero-credential disposable email client powered by Mail.tm REST API.

    Designed for automated email OTP and verification code retrieval in test pipelines.
    """

    BASE_URL: str = "https://api.mail.tm"

    def __init__(self) -> None:
        self.headers: dict[str, str] = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        }

    def _http_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: dict[str, object] | None = None,
        token: str | None = None,
    ) -> dict[str, object]:
        url = f"{self.BASE_URL}{endpoint}"
        payload = json.dumps(data).encode("utf-8") if data else None

        req_headers = dict(self.headers)
        if token:
            req_headers["Authorization"] = f"Bearer {token}"

        req = urllib.request.Request(url, data=payload, headers=req_headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp_text = resp.read().decode("utf-8")
                return json.loads(resp_text) if resp_text else {}
        except HTTPError as e:
            if e.code == 429:
                raise MailServiceRateLimitError(
                    "Public temp-mail API rate-limited (HTTP 429 Too Many Requests)."
                ) from e
            err_body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError(f"Mail.tm API error {e.code}: {err_body}") from e

    def get_available_domain(self) -> str:
        """Fetches active email domain."""
        res = self._http_request("/domains")
        members = res.get("hydra:member")
        if isinstance(members, list) and len(members) > 0:
            first = members[0]
            if isinstance(first, dict):
                domain = str(first.get("domain", "uberip.com"))
                return domain
        return "uberip.com"

    def create_inbox(self) -> tuple[str, str]:
        """Creates an on-the-fly inbox and returns (email_address, auth_token)."""
        domain = self.get_available_domain()
        suffix = random.randint(100000, 999999)
        address = f"stumble_qa_{suffix}@{domain}"
        password = f"P@ss_{suffix}_Secure!"
        logger.info("Provisioning disposable mailbox: %s", address)

        # Register account
        self._http_request(
            "/accounts",
            method="POST",
            data={"address": address, "password": password},
        )

        # Authenticate and retrieve JWT token
        token_res = self._http_request(
            "/token",
            method="POST",
            data={"address": address, "password": password},
        )
        token = str(token_res.get("token", ""))
        logger.info("Disposable mailbox provisioned successfully: %s", address)
        return address, token

    def wait_for_otp(
        self,
        token: str,
        timeout_sec: int = 60,
        otp_pattern: str = r"\b(\d{6})\b",
        min_created_at: datetime | None = None,
    ) -> str:
        """Polls inbox until an email arrives and extracts the 6-digit OTP code.

        Always reads the *newest* message first to avoid returning a stale OTP
        from a previous login attempt when the inbox has accumulated multiple emails.

        Args:
            token: Mail.tm JWT auth token for the inbox.
            timeout_sec: Maximum seconds to wait for an OTP email.
            otp_pattern: Regex pattern to extract the OTP code.
            min_created_at: If provided (a datetime), only accept emails created
                at or after this timestamp. Use this to ignore OTP emails from
                previous login sessions that are still in the inbox.
        """
        logger.info("Polling disposable mailbox for OTP email (timeout=%ds)...", timeout_sec)
        if min_created_at is not None:
            logger.info("Only accepting OTP emails created at or after: %s", min_created_at)
        start_time = time.monotonic()
        poll_interval_sec = 2.0

        while time.monotonic() - start_time < timeout_sec:
            messages_res = self._http_request("/messages", token=token)
            messages = messages_res.get("hydra:member")

            if isinstance(messages, list) and len(messages) > 0:
                # Sort newest-first so we always pick the OTP for the current
                # login attempt, not a stale code from an earlier attempt.
                sorted_messages = sorted(
                    [m for m in messages if isinstance(m, dict)],
                    key=lambda m: str(m.get("createdAt", "")),
                    reverse=True,
                )
                for msg in sorted_messages:
                    # Skip messages older than the current login attempt
                    if min_created_at is not None:
                        raw_ts = str(msg.get("createdAt", ""))
                        try:
                            msg_ts = datetime.fromisoformat(raw_ts)
                            if msg_ts.tzinfo is None:
                                msg_ts = msg_ts.replace(tzinfo=UTC)
                            if msg_ts < min_created_at:
                                logger.debug(
                                    "Skipping stale OTP email (createdAt=%s < min=%s)",
                                    raw_ts,
                                    min_created_at,
                                )
                                continue
                        except (ValueError, TypeError):
                            pass  # If we can't parse the timestamp, don't skip

                    msg_id = str(msg.get("id", ""))
                    msg_details = self._http_request(f"/messages/{msg_id}", token=token)
                    text_body = str(msg_details.get("text", "")) + " " + str(msg_details.get("intro", ""))

                    match = re.search(otp_pattern, text_body)
                    if match:
                        code = match.group(1)
                        logger.info(
                            "Extracted OTP verification code: %s (from message %s, createdAt=%s)",
                            code,
                            msg_id,
                            msg.get("createdAt", "unknown"),
                        )
                        return code

            poll_start = time.monotonic()
            while time.monotonic() - poll_start < poll_interval_sec:
                pass

        raise TimeoutError(f"No OTP email received within {timeout_sec}s.")

    def wait_for_verification_email(
        self,
        token: str,
        timeout_sec: int = 60,
    ) -> dict[str, str | None]:
        """Polls inbox until a verification email arrives and returns subject, body, OTP code, and confirmation URL."""
        logger.info("Polling disposable mailbox for verification email (timeout=%ds)...", timeout_sec)
        start_time = time.monotonic()
        poll_interval_sec = 2.0

        while time.monotonic() - start_time < timeout_sec:
            messages_res = self._http_request("/messages", token=token)
            messages = messages_res.get("hydra:member")

            if isinstance(messages, list) and len(messages) > 0:
                for msg in messages:
                    if not isinstance(msg, dict):
                        continue
                    msg_id = str(msg.get("id", ""))
                    msg_details = self._http_request(f"/messages/{msg_id}", token=token)
                    text_body = str(msg_details.get("text", "")) + " " + str(msg_details.get("intro", ""))
                    html_raw = msg_details.get("html", "")
                    html_content = "".join(html_raw) if isinstance(html_raw, list) else str(html_raw)

                    # Extract OTP if present (6 digits)
                    otp_match = re.search(r"\b(\d{6})\b", text_body)
                    otp_code = otp_match.group(1) if otp_match else None

                    # Extract confirmation / magic sign-in links
                    auth_links = re.findall(r"href=[\x27\x22](https://[^\x27\x22\s]+)[\x27\x22]", html_content)
                    confirm_url = None
                    auth_keywords = ["verify", "confirm", "token", "auth", "signin", "signup", "callback"]
                    for link in auth_links:
                        if any(k in link.lower() for k in auth_keywords):
                            confirm_url = link
                            break
                    if not confirm_url and auth_links:
                        ignored_exts = [".png", ".jpg", ".svg", ".css"]
                        for link in auth_links:
                            if "scopely" in link.lower() and not any(ext in link.lower() for ext in ignored_exts):
                                confirm_url = link
                                break
                    if not confirm_url and auth_links:
                        confirm_url = auth_links[0]

                    # Also check plain text body for URL if HTML had no auth links
                    if not confirm_url:
                        text_url_match = re.search(r"(https://id\.scopely\.com[^\s]+)", text_body)
                        if text_url_match:
                            confirm_url = text_url_match.group(1)

                    subject_str = str(msg.get("subject", ""))
                    logger.info(
                        "Verification message received! Subject: %s | Confirm URL: %s",
                        subject_str,
                        confirm_url,
                    )
                    return {
                        "subject": subject_str,
                        "text": text_body,
                        "otp": otp_code,
                        "confirm_url": confirm_url,
                    }

            poll_start = time.monotonic()
            while time.monotonic() - poll_start < poll_interval_sec:
                pass

        raise TimeoutError(f"No verification email received within {timeout_sec}s.")
