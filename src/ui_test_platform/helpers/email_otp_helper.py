from __future__ import annotations

import json
import random
import re
import time
import urllib.request
from urllib.error import HTTPError


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
        return address, token

    def wait_for_otp(
        self,
        token: str,
        timeout_sec: int = 60,
        otp_pattern: str = r"\b(\d{6})\b",
    ) -> str:
        """Polls inbox until an email arrives and extracts the 6-digit OTP code."""
        start_time = time.monotonic()
        poll_interval_sec = 2.0

        while time.monotonic() - start_time < timeout_sec:
            messages_res = self._http_request("/messages", token=token)
            messages = messages_res.get("hydra:member")

            if isinstance(messages, list) and len(messages) > 0:
                # Latest message
                latest_msg = messages[0]
                if isinstance(latest_msg, dict):
                    msg_id = str(latest_msg.get("id", ""))
                    # Fetch full email message body
                    msg_details = self._http_request(f"/messages/{msg_id}", token=token)
                    text_body = str(msg_details.get("text", "")) + " " + str(msg_details.get("intro", ""))

                    match = re.search(otp_pattern, text_body)
                    if match:
                        return match.group(1)

            # Monotonic poll delay without thread sleep
            slice_start = time.monotonic()
            while time.monotonic() - slice_start < poll_interval_sec:
                pass

        raise TimeoutError(f"No OTP email received within {timeout_sec}s.")
