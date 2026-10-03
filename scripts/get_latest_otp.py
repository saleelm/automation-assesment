#!/usr/bin/env python3
"""CLI utility to retrieve or live-wait for the latest Scopely Account OTP code.

Usage:
    PYTHONPATH=src .venv/bin/python scripts/get_latest_otp.py
    PYTHONPATH=src .venv/bin/python scripts/get_latest_otp.py --wait
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime

from ui_test_platform.helpers.email_otp_helper import TempMailClient
from ui_test_platform.helpers.user_credential_store import load_test_user


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch or wait for latest Scopely OTP code")
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Poll and wait for a new incoming OTP code arriving after this script starts",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout in seconds when waiting for new OTP (default: 60)",
    )
    args = parser.parse_args()

    user = load_test_user()
    if not user:
        print("❌ No verified test user found in playwright/.auth/test_user.json", file=sys.stderr)
        sys.exit(1)

    email = user["email"]
    mail_token = user["mail_token"]
    print(f"📧 Test user email: {email}")

    client = TempMailClient()

    if args.wait:
        t0 = datetime.now(tz=UTC)
        print(f"⏳ Waiting up to {args.timeout}s for incoming OTP code sent to {email}...")
        try:
            code = client.wait_for_otp(token=mail_token, timeout_sec=args.timeout, min_created_at=t0)
            print(f"\n🔑 Latest OTP Code: {code}")
        except Exception as e:
            print(f"❌ Failed to receive OTP: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Fetch current latest OTP from inbox
        try:
            code = client.wait_for_otp(token=mail_token, timeout_sec=5)
            print(f"🔑 Latest OTP Code in inbox: {code}")
        except Exception:
            print("ℹ️ No recent OTP code found in inbox. Use --wait to listen for incoming OTP.")


if __name__ == "__main__":
    main()
