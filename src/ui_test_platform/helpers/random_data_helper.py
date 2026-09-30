from __future__ import annotations

import random
import string
import time


class RandomDataHelper:
    """Helper to generate randomized test data for forms, users, and transactions."""

    @staticmethod
    def random_string(prefix: str = "test_", length: int = 8) -> str:
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
        return f"{prefix}{suffix}"

    @staticmethod
    def random_email(domain: str = "example.com") -> str:
        timestamp = int(time.time())
        suffix = "".join(random.choices(string.ascii_lowercase, k=4))
        return f"user_{timestamp}_{suffix}@{domain}"

    @staticmethod
    def random_username(prefix: str = "Stumbler_") -> str:
        num = random.randint(1000, 99999)
        return f"{prefix}{num}"
