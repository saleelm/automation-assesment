#!/usr/bin/env python3
"""Interactive Session Saver for Stumble Guys UI Automation Platform.

Launches a visible browser window allowing you to log in with your email and
6-digit OTP code, then extracts and saves cookies/storageState into
playwright/.auth/userSession.json for subsequent automated test runs.
"""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> None:
    auth_dir = Path("playwright/.auth")
    auth_dir.mkdir(parents=True, exist_ok=True)
    session_file = auth_dir / "userSession.json"

    print("\n=======================================================")
    print("🚀 Stumble Guys - Interactive Auth Session Bootstrapper")
    print("=======================================================\n")
    print("1. A visible Chrome browser window will now open.")
    print("2. Enter your email, receive your 6-digit OTP, and submit it.")
    print("3. Once logged in, return here and press [ENTER] to save.\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        page.goto("https://www.stumbleguys.com/", wait_until="domcontentloaded")

        try:
            # Trigger login menu if visible
            avatar_btn = page.locator("button:has(img[alt='avatar']):visible").first
            if avatar_btn.is_visible(timeout=3000):
                avatar_btn.click()
                login_btn = page.locator("button:has-text('Login'):visible").first
                if login_btn.is_visible(timeout=2000):
                    login_btn.click()
        except Exception:
            pass

        print("👉 Complete your login in the browser window now.")
        input("👉 Press [ENTER] in this terminal once you are logged in: ")

        # Save session state
        context.storage_state(path=str(session_file))
        print(f"\n✅ Authenticated session successfully saved to: {session_file}")
        print("🎉 You can now run tests with your logged-in account: pytest --platform web\n")
        browser.close()


if __name__ == "__main__":
    main()
