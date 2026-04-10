"""
Opponent scouting entry point.

Accepts an opponent team URL or numeric team ID, fetches their squad from
PManager, and cross-references it against the local player database to
identify players already on the watchlist.

Usage::

    python main_opponent_scout.py <TEAM_URL_OR_ID>

Examples::

    python main_opponent_scout.py 12345
    python main_opponent_scout.py https://www.pmanager.org/ver_equipa.asp?equipa=12345
"""

import argparse
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

from src.config import config
from src.core.logger import logger
from src.scrapers.opponent import OpponentScraper
from src.services.supabase_client import SupabaseManager

_BASE_URL = "https://www.pmanager.org"


def _resolve_team_url(input_arg: str) -> str | None:
    """Convert a team ID or URL to a full team roster URL.

    Args:
        input_arg: Either a numeric team ID string or a full PManager URL.

    Returns:
        Full roster URL string, or ``None`` if the input is unrecognisable.
    """
    if _BASE_URL in input_arg:
        # Ensure vjog=1 is present so the squad/player list view is shown
        if "vjog=1" not in input_arg:
            separator = "&" if "?" in input_arg else "?"
            return f"{input_arg}{separator}vjog=1"
        return input_arg
    if input_arg.isdigit():
        return f"{_BASE_URL}/ver_equipa.asp?equipa={input_arg}&vjog=1"
    return None


def main() -> None:
    """Run the opponent scout and print a match report."""
    parser = argparse.ArgumentParser(
        description="Scout an opponent team and cross-reference with your player database."
    )
    parser.add_argument(
        "team",
        help="Opponent team ID (numeric) or full PManager team URL.",
    )
    args = parser.parse_args()

    config.validate()

    team_url = _resolve_team_url(args.team)
    if not team_url:
        logger.error(
            "Invalid input '%s'. Provide a numeric team ID or a full pmanager.org URL.",
            args.team,
        )
        return

    team_id = parse_qs(urlparse(team_url).query).get("equipa", ["unknown"])[0]
    logger.info("Starting Opponent Scout for: %s (team_id=%s)", team_url, team_id)

    db = SupabaseManager()
    existing_records = db.get_all_players()
    existing_ids = {str(r["id"]) for r in existing_records if "id" in r}
    logger.info("Loaded %d players from database.", len(existing_ids))

    scraper = OpponentScraper(base_url=_BASE_URL)

    try:
        scraper.start(headless=config.HEADLESS_MODE)
        scraper.login(config.PM_USERNAME, config.PM_PASSWORD)

        team_name, opponent_players = scraper.get_team_players(team_url)

        if not opponent_players:
            logger.warning("No players found on this team page.")
            return

        opponent_ids = {p["player_id"] for p in opponent_players}
        matches = opponent_ids & existing_ids

        logger.info("=" * 50)
        logger.info(
            "SCOUT REPORT — %s (team_id=%s) — %d players found, %d watchlist matches",
            team_name or "Unknown Team",
            team_id,
            len(opponent_players),
            len(matches),
        )
        logger.info("=" * 50)

        scouted_at = datetime.now(timezone.utc).isoformat()
        results_to_save = []
        for p in opponent_players:
            pid = p["player_id"]
            is_match = pid in matches
            if is_match:
                logger.info("  [MATCH] [%s] %s (ID: %s)", p["position"], p["name"], pid)
            results_to_save.append({
                "team_id": team_id,
                "player_id": pid,
                "team_name": team_name,
                "player_name": p["name"] or None,
                "position": p["position"] or None,
                "age": p["age"] or None,
                "quality": p["quality"] or None,
                "player_link": f"{_BASE_URL}/ver_jogador.asp?jog_id={pid}",
                "scouted_at": scouted_at,
                "is_watchlist_match": is_match,
            })

        db.delete_opponent_scout_results_by_team(team_id)
        db.upsert_opponent_scout_results(results_to_save)
        logger.info("Saved %d players to opponent_scout_results.", len(results_to_save))
        logger.info("=" * 50)

    except Exception as e:
        logger.error("An error occurred: %s", e, exc_info=True)
    finally:
        scraper.stop()


if __name__ == "__main__":
    main()
