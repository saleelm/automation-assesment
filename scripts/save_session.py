#!/usr/bin/env python3
"""Interactive Session Saver for Stumble Guys UI Automation Platform.

Launches a visible browser window allowing you to log in or load the WebGL
game portal (/play), then saves cookies, localStorage, and session state into
playwright/.auth/userSession.json (and persistent browser profile) for subsequent
automated test runs so tests see the direct "PLAY" button.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> None:
    parser = argparse.ArgumentParser(description="Stumble Guys Session Saver")
    parser.add_argument(
        "--game",
        action="store_true",
        help="Navigate to /play WebGL game portal to persist game session & cookies",
    )
    parser.add_argument(
        "--persistent",
        action="store_true",
        help="Persist full browser user profile directory (includes IndexedDB & WebGL cache)",
    )
    args = parser.parse_args()

    auth_dir = Path("playwright/.auth")
    auth_dir.mkdir(parents=True, exist_ok=True)
    session_file = auth_dir / "userSession.json"
    profile_dir = auth_dir / "browser_profile"

    target_url = "https://www.stumbleguys.com/play" if args.game else "https://www.stumbleguys.com/"

    print("\n=======================================================")
    print("🚀 Stumble Guys - Interactive Session & Cookie Saver")
    print("=======================================================\n")
    print(f"Target URL: {target_url}")
    print("1. A visible Chrome browser window will now open.")
    if args.game:
        print("2. Wait for the game assets to finish loading and verify the direct PLAY button.")
        print("   (Accept any cookie consent or onboarding prompts if presented.)")
    else:
        print("2. Log in with your email/OTP or navigate to the game portal.")
    print("3. Return to this terminal and press [ENTER] to save your session.\n")

    with sync_playwright() as p:
        if args.persistent:
            profile_dir.mkdir(parents=True, exist_ok=True)
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(profile_dir),
                headless=False,
                viewport={"width": 1280, "height": 800},
            )
            page = context.pages[0] if context.pages else context.new_page()
        else:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()

        page.goto(target_url, wait_until="domcontentloaded")

        if not args.game:
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

        print("👉 Complete your actions in the browser window now.")
        input("👉 Press [ENTER] in this terminal once ready to save session: ")

        # Save session state
        context.storage_state(path=str(session_file))
        print(f"\n✅ Session state successfully saved to: {session_file}")
        if args.persistent:
            print(f"✅ Persistent browser profile saved to: {profile_dir}")
        print("🎉 You can now run tests with your persisted state: pytest --platform web\n")
        context.close()
        if not args.persistent:
            browser.close()


if __name__ == "__main__":
    main()
