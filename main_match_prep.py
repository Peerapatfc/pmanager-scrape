"""Analyze an upcoming opponent: scrape last 10 matches, enrich roster, store analysis."""
import sys

from src.config import config
from src.core.logger import logger
from src.scrapers.match_prep import MatchPrepScraper
from src.services.supabase_client import SupabaseManager


def main(opponent_team_id: str, season: str) -> None:
    """Analyze an opponent team's recent performance and roster.

    Args:
        opponent_team_id: PManager team ID of the opponent.
        season: Season code for the current league.
    """
    config.validate()
    logger.info("Analyzing opponent %s for season %s", opponent_team_id, season)

    sm = SupabaseManager()
    team_info = sm.get_team_info()
    my_team_name = team_info.get("team_name", "") if team_info else ""

    scraper = MatchPrepScraper()
    scraper.start(headless=True)
    try:
        scraper.login(config.PM_USERNAME, config.PM_PASSWORD)
        analysis = scraper.build_analysis(opponent_team_id, season, my_team_name, sm)
    finally:
        scraper.stop()

    sm.upsert_fixture_analysis(analysis)
    logger.info("Analysis stored for %s", analysis.get("opponent_team_name"))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python main_match_prep.py <opponent_team_id> <season>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
