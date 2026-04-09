"""
Central configuration for pmanager-scrape.

Reads all required environment variables from the .env file and exposes them
via the ``Config`` class. Call ``Config.validate()`` at the top of any entry
script to fail fast if a required variable is missing.
"""

import os
import sys

from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Config:
    """Application-wide configuration loaded from environment variables."""

    # PManager game credentials
    PM_USERNAME: str | None = os.getenv("PM_USERNAME")
    PM_PASSWORD: str | None = os.getenv("PM_PASSWORD")

    # Supabase
    SUPABASE_URL: str | None = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: str | None = os.getenv("SUPABASE_KEY")

    # Telegram
    TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: str | None = os.getenv("TELEGRAM_CHAT_ID")
    SCOUT_BOT_TOKEN: str | None = os.getenv("SCOUT_BOT_TOKEN")

    # GitHub Actions (optional — only needed for workflow dispatch)
    GITHUB_TOKEN: str | None = os.getenv("GITHUB_TOKEN")
    GITHUB_REPO: str | None = os.getenv("GITHUB_REPO")

    # Google Sheets (legacy, kept for backward compatibility)
    GOOGLE_CREDENTIALS_FILE: str = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    SPREADSHEET_ID: str | None = os.getenv("SPREADSHEET_ID")
    SHEET_NAME_ALL_PLAYERS: str = "All Players"
    SHEET_NAME_TRANSFER_INFO: str = "Transfer Info"

    # Season
    CURRENT_SEASON: str = os.getenv("CURRENT_SEASON", "99")

    # Browser
    HEADLESS_MODE: bool = True

    @classmethod
    def validate(cls) -> None:
        """Validate that all required environment variables are set.

        Logs descriptive error messages and exits with code 1 if any required
        variable is missing or empty.
        """
        errors: list[str] = []

        if not cls.PM_USERNAME or not cls.PM_PASSWORD:
            errors.append("PM_USERNAME and PM_PASSWORD are required (PManager game credentials)")

        if not cls.SUPABASE_URL or not cls.SUPABASE_KEY:
            errors.append("SUPABASE_URL and SUPABASE_KEY are required (database connection)")

        if errors:
            for msg in errors:
                print(f"[Config] ERROR: {msg}", file=sys.stderr)
            print("[Config] Set missing variables in your .env file.", file=sys.stderr)
            sys.exit(1)

    @classmethod
    def validate_telegram(cls) -> None:
        """Validate that Telegram credentials are set.

        Call this in scripts that send Telegram notifications.
        """
        if not cls.TELEGRAM_BOT_TOKEN or not cls.TELEGRAM_CHAT_ID:
            print(
                "[Config] ERROR: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required",
                file=sys.stderr,
            )
            sys.exit(1)


config = Config()
