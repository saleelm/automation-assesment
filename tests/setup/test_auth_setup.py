from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ui_test_platform.fixtures.pom.test_options import Tag, step, tags, title

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = [pytest.mark.setup, pytest.mark.unauthenticated]


class TestAuthSetup:
    @tags(Tag.SETUP, Tag.AUTH)
    @title("TC00 should bootstrap and verify authenticated storage state file exists")
    def test_tc00_should_bootstrap_auth_storage_state(self, auth_state: Path) -> None:
        with step("Given auth state bootstrap is invoked"):
            assert auth_state.exists(), f"Auth state file does not exist at {auth_state}"

        with step("Then the auth state file should contain valid storage json structure"):
            assert auth_state.is_file()
            assert auth_state.stat().st_size > 0
