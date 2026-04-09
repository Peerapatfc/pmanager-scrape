"""Scrape my team's upcoming fixture list and sync to upcoming_fixtures table."""

from src.config import config
from src.core.logger import logger
from src.scrapers.match_prep import MatchPrepScraper
from src.services.supabase_client import SupabaseManager


def main() -> None:
    """Sync upcoming fixtures for the current season to Supabase."""
    config.validate()
    season = config.CURRENT_SEASON
    logger.info("Syncing fixtures for season %s", season)

    sm = SupabaseManager()
    scraper = MatchPrepScraper()
    scraper.start(headless=True)
    try:
        scraper.login(config.PM_USERNAME, config.PM_PASSWORD)
        fixtures = scraper.scrape_my_fixtures(season)
    finally:
        scraper.stop()

    logger.info("Scraped %d fixtures", len(fixtures))
    sm.upsert_upcoming_fixtures(fixtures)
    logger.info("Fixture sync complete")


if __name__ == "__main__":
    main()
