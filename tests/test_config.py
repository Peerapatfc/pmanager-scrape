"""
Unit tests for src.config — Config.validate() and Config.validate_telegram().

These tests monkeypatch environment variables to avoid requiring a real .env
file during CI. No external services are contacted.
"""

import sys

import pytest


class TestConfigValidate:
    """Tests for Config.validate()."""

    def test_valid_config_does_not_exit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """validate() should not exit when all required vars are set."""
        monkeypatch.setenv("PM_USERNAME", "user")
        monkeypatch.setenv("PM_PASSWORD", "pass")
        monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "key")

        # Re-import config to pick up the patched env vars
        import importlib

        import src.config as cfg_module

        importlib.reload(cfg_module)

        # Should not raise SystemExit
        cfg_module.Config.validate()

    def test_missing_pm_credentials_exits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("PM_USERNAME", raising=False)
        monkeypatch.delenv("PM_PASSWORD", raising=False)
        monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "key")

        import importlib

        import src.config as cfg_module

        importlib.reload(cfg_module)

        with pytest.raises(SystemExit):
            cfg_module.Config.validate()

    def test_missing_supabase_credentials_exits(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("PM_USERNAME", "user")
        monkeypatch.setenv("PM_PASSWORD", "pass")
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_KEY", raising=False)

        import importlib

        import src.config as cfg_module

        importlib.reload(cfg_module)

        with pytest.raises(SystemExit):
            cfg_module.Config.validate()


class TestConfigValidateTelegram:
    """Tests for Config.validate_telegram()."""

    def test_valid_telegram_config_does_not_exit(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token123")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat456")

        import importlib

        import src.config as cfg_module

        importlib.reload(cfg_module)
        cfg_module.Config.validate_telegram()  # Should not raise

    def test_missing_telegram_token_exits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat456")

        import importlib

        import src.config as cfg_module

        importlib.reload(cfg_module)

        with pytest.raises(SystemExit):
            cfg_module.Config.validate_telegram()
