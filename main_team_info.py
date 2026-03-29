"""
Team info scraper entry point.

Scrapes the manager's own team information page (``/info.asp``) and uploads
the snapshot to the ``team_info`` table in Supabase. Also saves a JSON file
locally for quick inspection.

Usage::

    python main_team_info.py
"""

import json
from datetime import datetime

from src.config import config
from src.core.logger import logger
from src.scrapers.team import TeamInfoScraper
from src.services.supabase_client import SupabaseManager

#: Local filename for the JSON snapshot backup.
OUTPUT_FILE = "team_info.json"


def main() -> None:
    """Scrape team info and upload to Supabase."""
    config.validate()

    logger.info("Starting Team Info Scraper...")
    scraper = TeamInfoScraper()

    try:
        scraper.start(headless=config.HEADLESS_MODE)
        scraper.login(config.PM_USERNAME, config.PM_PASSWORD)

        info = scraper.get_team_info()

        logger.info("=" * 50)
        logger.info("TEAM INFORMATION")
        logger.info("=" * 50)
        for key, value in info.items():
            if not key.endswith("_int"):
                logger.info("%s: %s", key.replace("_", " ").title(), value)
        logger.info("=" * 50)

        # Save JSON backup
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(info, f, indent=4, ensure_ascii=False)
        logger.info("Saved team info to %s", OUTPUT_FILE)

        # Upload to Supabase
        db = SupabaseManager()
        db.upsert_team_info(info)

    except Exception as e:
        logger.error("An error occurred: %s", e, exc_info=True)
    finally:
        scraper.stop()


if __name__ == "__main__":
    main()
