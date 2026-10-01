from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from dotenv import load_dotenv

from ui_test_platform.enums.tags import Platform, Tag

if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.config.argparsing import Parser
    from _pytest.main import Session
    from _pytest.nodes import Item

# 1. Load env before AppConfig is imported
_env_slug = os.getenv("ENVIRONMENT", "qa").strip()
_env_file = Path(__file__).parent / "env" / f".env.{_env_slug}"
if _env_file.exists():
    load_dotenv(_env_file, override=False)
else:
    # Fallback to .env.local if exists
    _local_file = Path(__file__).parent / "env" / ".env.local"
    if _local_file.exists():
        load_dotenv(_local_file, override=False)


def pytest_addoption(parser: Parser) -> None:
    default_platform = os.getenv("PLATFORM", Platform.WEB.value)
    parser.addoption(
        "--platform",
        action="store",
        default=default_platform,
        choices=[p.value for p in Platform],
        help="Target platform: web, mobile-emulated, android-device",
    )


def pytest_configure(config: Config) -> None:
    # Register all enum tags as strict markers
    for tag in Tag:
        config.addinivalue_line("markers", f"{tag.value}: mark test with {tag.value}")

    # TestRail JUnit export if enabled
    if os.getenv("TESTRAIL_ENABLED", "false").lower() == "true":
        results_dir = Path("junit-results")
        results_dir.mkdir(parents=True, exist_ok=True)
        config.option.xmlpath = str(results_dir / "results.xml")


logger = logging.getLogger("ui_test_platform.runner")


def pytest_runtest_setup(item: Item) -> None:
    logger.info("▶▶ STARTING TEST: %s", item.nodeid)


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    if report.when == "call":
        if report.passed:
            logger.info("✔✔ PASSED TEST: %s", report.nodeid)
        elif report.failed:
            logger.error("✖✖ FAILED TEST: %s", report.nodeid)
        elif report.skipped:
            logger.warning("⚠⚠ SKIPPED TEST: %s", report.nodeid)


def pytest_collection_modifyitems(config: Config, items: list[Item]) -> None:
    platform_opt = config.getoption("--platform")
    current_platform = Platform(platform_opt) if platform_opt else Platform.WEB

    for item in items:
        # Cross-platform skipping logic
        if current_platform.is_mobile and item.get_closest_marker(Tag.WEB_ONLY.value):
            item.add_marker(pytest.mark.skip(reason=f"Skipped on mobile: {Tag.WEB_ONLY.value}"))
        elif not current_platform.is_mobile and item.get_closest_marker(Tag.MOBILE_ONLY.value):
            item.add_marker(pytest.mark.skip(reason=f"Skipped on desktop web: {Tag.MOBILE_ONLY.value}"))


def pytest_sessionfinish(session: Session, exitstatus: int) -> None:
    # Only write on controller in xdist runs
    if not hasattr(session.config, "workerinput"):
        allure_dir = Path("allure-results")
        allure_dir.mkdir(parents=True, exist_ok=True)
        env_props_file = allure_dir / "environment.properties"

        platform_val = session.config.getoption("--platform") or os.getenv("PLATFORM", "web")
        device_val = os.getenv("MOBILE_DEVICE", "Pixel 7")
        browser_val = session.config.getoption("--browser", default=["chromium"])
        env_val = os.getenv("ENVIRONMENT", "qa")
        base_url_val = os.getenv("BASE_URL", "https://www.stumbleguys.com")

        content = (
            f"Environment={env_val}\n"
            f"Platform={platform_val}\n"
            f"Device={device_val if platform_val != 'web' else 'Desktop'}\n"
            f"Browser={browser_val}\n"
            f"BaseURL={base_url_val}\n"
        )
        env_props_file.write_text(content, encoding="utf-8")
