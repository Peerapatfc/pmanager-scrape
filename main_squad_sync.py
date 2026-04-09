"""
Squad sync — scrapes plantel.asp and updates Supabase.

Reads the user's full squad from PManager, upserts player skills into the
``players`` table, and refreshes the ``my_squad`` membership table so the
dashboard reflects the current squad.
"""

from src.config import config
from src.core.logger import logger
from src.scrapers.squad import SKILL_COLUMNS, SquadScraper
from src.services.supabase_client import SupabaseManager


def main() -> None:
    config.validate()

    scraper = SquadScraper()
    logger.info("Starting squad sync...")

    records = scraper.scrape()

    if not records:
        logger.warning("No players returned from squad scraper — aborting.")
        return

    db = SupabaseManager()

    # Build player records for upsert into `players` table.
    # upsert_players expects "id" and treats unknown keys as skills.
    player_records = []
    for r in records:
        rec: dict = {
            "id": r["player_id"],
            "name": r["name"],
            "position": r["position"],
            "age": r["age"],
        }
        for skill in SKILL_COLUMNS:
            if skill in r:
                rec[skill] = r[skill]
        player_records.append(rec)

    db.upsert_players(player_records)

    # Refresh my_squad membership.
    squad_records = [
        {"player_id": r["player_id"], "position": r["position"]}
        for r in records
    ]
    db.upsert_my_squad(squad_records)

    logger.info("Squad sync complete — %d players synced.", len(records))


if __name__ == "__main__":
    main()
