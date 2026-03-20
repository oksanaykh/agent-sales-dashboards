"""
config/settings.py

Reads configuration from environment variables / .env file.
All values have sensible defaults so the agent works out of the box.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path


class Settings:
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    reports_dir: str = os.getenv("REPORTS_DIR", "reports")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    def __post_init__(self):
        Path(self.reports_dir).mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    s = Settings()
    Path(s.reports_dir).mkdir(parents=True, exist_ok=True)
    return s
