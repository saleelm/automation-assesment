#!/usr/bin/env python3
"""Interactive Session Saver for Stumble Guys UI Automation Platform.

Launches a visible browser window allowing you to log in with your email and
6-digit OTP code, then extracts and saves cookies/storageState into
playwright/.auth/userSession.json for subsequent automated test runs.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> None:
    parser = argparse.ArgumentParser(description="Stumble Guys Auth Session Saver")
    parser.add_argument(
        "--provider",
        choices=["email", "facebook"],
        default=os.getenv("LOGIN_PROVIDER", "email").lower(),
        help="Login provider to use (default: email, or from LOGIN_PROVIDER env var)",
    )
    args = parser.parse_args()

    auth_dir = Path("playwright/.auth")
    auth_dir.mkdir(parents=True, exist_ok=True)
    session_file = auth_dir / "userSession.json"

    print("\n=======================================================")
    print(f"🚀 Stumble Guys - Auth Bootstrapper (Provider: {args.provider.upper()})")
    print("=======================================================\n")
    print("1. A visible Chrome browser window will now open.")
    if args.provider == "facebook":
        print("2. Enter your Facebook credentials and authorize.")
    else:
        print("2. Enter your email, receive your 6-digit OTP, and submit it.")
    print("3. Once logged in on the portal, return here and press [ENTER] to save.\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        page.goto("https://www.stumbleguys.com/", wait_until="domcontentloaded")

        try:
            # Trigger login menu
            avatar_btn = page.locator("button:has(img[alt='avatar']):visible").first
            if avatar_btn.is_visible(timeout=3000):
                avatar_btn.click()
                login_btn = page.locator("button:has-text('Login'):visible").first
                if login_btn.is_visible(timeout=2000):
                    login_btn.click()

            if args.provider == "facebook":
                fb_btn = page.locator(
                    "button:has-text('Facebook'):visible, button:has(img[alt*='facebook' i]):visible"
                ).first
                if fb_btn.is_visible(timeout=3000):
                    fb_btn.click()
            else:
                email_btn = page.locator("button:has-text('Continue with email'):visible").first
                if email_btn.is_visible(timeout=3000):
                    email_btn.click()
        except Exception:
            pass

        print(f"👉 Complete your {args.provider.upper()} login in the browser window now.")
        input("👉 Press [ENTER] in this terminal once you are logged in: ")

        # Save session state
        context.storage_state(path=str(session_file))
        print(f"\n✅ Authenticated session successfully saved to: {session_file}")
        print("🎉 You can now run tests with your logged-in account: pytest --platform web\n")
        browser.close()


if __name__ == "__main__":
    main()
