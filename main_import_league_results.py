"""Scrape PManager league match reports → upsert to league_match_results.

Usage:
    python main_import_league_results.py [--season 99] [--round 12]
    python main_import_league_results.py --season 99 --round 12 --force

Options:
    --season N   Season number (default: 99)
    --round N    Only process one round (omit for all unimported matches)
    --div N      Division (default: 1)
    --serie N    Serie (default: 1)
    --pages N    Fixture pages to scan (default: 3)
    --force      Re-scrape game_ids already in DB
"""

from __future__ import annotations

import argparse
import re

from src.config import config
from src.core.logger import logger
from src.scrapers.league_fixtures import LeagueFixturesScraper
from src.services.supabase_client import SupabaseManager


def _round_key(date_iso: str, competition: str) -> str:
    safe = re.sub(r"[^\w\-]", "_", competition).strip("_") or "Unknown"
    return f"{date_iso}___{safe}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Import league match reports to Supabase")
    parser.add_argument("--season", type=int, default=99)
    parser.add_argument("--round",  type=int, default=None, dest="round_num")
    parser.add_argument("--div",    type=int, default=1)
    parser.add_argument("--serie",  type=int, default=1)
    parser.add_argument("--pages",  type=int, default=3)
    parser.add_argument("--force",  action="store_true",
                        help="Re-import game_ids already in DB")
    args = parser.parse_args()

    config.validate()
    sm = SupabaseManager()

    existing_ids: set[str] = set()
    if not args.force:
        existing_ids = set(sm.get_all_league_match_game_ids())
        logger.info("%d game_ids already in DB", len(existing_ids))

    with LeagueFixturesScraper() as scraper:
        scraper.login(config.pm_username, config.pm_password)

        fixtures = scraper.get_season_fixtures(
            season=args.season,
            div=args.div,
            serie=args.serie,
            pages=args.pages,
        )
        logger.info("Found %d played fixtures for season %d", len(fixtures), args.season)

        if args.round_num is not None:
            fixtures = [f for f in fixtures if f["round_num"] == args.round_num]
            logger.info("Filtered to round %d: %d fixtures", args.round_num, len(fixtures))

        to_scrape = [f for f in fixtures if f["game_id"] not in existing_ids]
        logger.info("%d fixtures to scrape", len(to_scrape))

        if not to_scrape:
            logger.info("Nothing new to import.")
            return

        records = []
        for fix in to_scrape:
            result = scraper.get_match_report(fix["game_id"])
            if result is None:
                logger.warning("MISSING  game_id=%s — skipping", fix["game_id"])
                continue

            competition = result.get("competition") or "Thai League"
            date_iso    = result.get("match_date") or fix.get("date") or ""
            rkey        = _round_key(date_iso, competition)

            record = {
                **result,
                "round_key": rkey,
            }
            records.append(record)
            logger.info(
                "OK  game_id=%-10s  %s %d-%d %s  (rnd %s)",
                fix["game_id"],
                result.get("home_team", "?"),
                result.get("home_score", 0),
                result.get("away_score", 0),
                result.get("away_team", "?"),
                fix.get("round_num", "?"),
            )

        if records:
            sm.upsert_league_match_results(records)
            logger.info("Upserted %d records to league_match_results.", len(records))
        else:
            logger.info("No records upserted.")


if __name__ == "__main__":
    main()
