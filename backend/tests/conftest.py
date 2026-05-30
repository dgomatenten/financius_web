"""
Root test configuration.

Sets DATABASE_URL to in-memory SQLite before any Flask module is imported,
clearing the lru_cache so create_app() picks up the test URL.
"""
import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from config.settings import get_settings  # noqa: E402
get_settings.cache_clear()
