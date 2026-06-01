"""
Root test configuration.

Sets DATABASE_URL to in-memory SQLite before any Flask module is imported,
clearing the lru_cache so create_app() picks up the test URL.
"""
import os
from importlib import import_module

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

try:
	# Legacy Flask test bootstrap; absent in Django-only test runs.
	get_settings = import_module("config.settings").get_settings
	get_settings.cache_clear()
except ModuleNotFoundError:
	pass
