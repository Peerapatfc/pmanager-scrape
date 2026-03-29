"""
BOT team discovery entry point.

Traverses all countries and the top :data:`~src.constants.MAX_DIVISION`
divisions in PManager to identify AI-controlled (BOT) teams and extract
their full rosters. Player stubs (id + team_name) are written to
``bot_opportunities`` in Supabase for later evaluation by
``main_bot_evaluate.py``.

A CSV backup is also written to ``bot_opportunities.csv``.

Usage::

    python main_bot_scout.py
"""

from datetime import datetime

import pandas as pd

from src import constants
from src.config import config
from src.core.logger import logger
from src.scrapers.bot_team import BotTeamScraper
from src.services.supabase_client import SupabaseManager


def main() -> None:
    """Run the full BOT team discovery and populate the evaluation queue."""
    config.validate()

    scraper = BotTeamScraper(base_url="https://www.pmanager.org")
    scraper.start(headless=config.HEADLESS_MODE)

    bot_opportunities = []

    try:
        scraper.login(config.PM_USERNAME, config.PM_PASSWORD)

        logger.info("Starting BOT Team Scrape (top %d divisions)...", constants.MAX_DIVISION)
        bot_teams = scraper.scrape_league_tree(max_division=constants.MAX_DIVISION)

        if not bot_teams:
            logger.warning("No BOT teams found!")
            return

        logger.info("Found %d total BOT teams. Extracting rosters...", len(bot_teams))

        for team in bot_teams:
            logger.debug(
                "Getting roster for %s (%s D%s)",
                team["name"],
                team["country"],
                team["division"],
            )
            pids = scraper.get_team_roster(team["id"])
            for pid in pids:
                bot_opportunities.append({"id": pid, "team_name": team["name"]})

        logger.info("Loaded %d players from BOT teams.", len(bot_opportunities))

    except Exception as e:
        logger.error("Global scraper error: %s", e, exc_info=True)
    finally:
        scraper.stop()

    if not bot_opportunities:
        logger.warning("No BOT player stubs to upload.")
        return

    df = pd.DataFrame(bot_opportunities)
    df["scraped_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    csv_file = "bot_opportunities.csv"
    df.to_csv(csv_file, index=False)
    logger.info("Saved CSV backup to %s", csv_file)

    db = SupabaseManager()
    db.clear_bot_opportunities()
    db.upsert_bot_opportunities(df.to_dict(orient="records"))


if __name__ == "__main__":
    main()
