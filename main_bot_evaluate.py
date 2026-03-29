"""
BOT player evaluation entry point.

Fetches a batch of the oldest-evaluated players from the ``bot_opportunities``
table and visits each player's page to extract up-to-date financial and
attribute data. Results are upserted back to Supabase.

The ``last_evaluated_at`` timestamp is updated for every player in the batch
(including those that return no data) so the continuous evaluation cycle
never gets stuck on invalid player IDs.

Batch size defaults to :data:`~src.constants.BOT_EVAL_BATCH_SIZE` (~2,200
players per daily run, calibrated to stay within GitHub Actions free-tier
minutes).

A CSV backup is written to ``bot_evaluations_batch.csv``.

Usage::

    python main_bot_evaluate.py
"""

from datetime import datetime

import pandas as pd

from src import constants
from src.config import config
from src.core.logger import logger
from src.scrapers.bot_team import BotTeamScraper
from src.services.supabase_client import SupabaseManager


def main() -> None:
    """Evaluate a batch of BOT players and update Supabase."""
    config.validate()

    scraper = BotTeamScraper(base_url="https://www.pmanager.org")
    scraper.start(headless=config.HEADLESS_MODE)

    db = SupabaseManager()

    players_batch = db.get_batch_for_evaluation(batch_size=constants.BOT_EVAL_BATCH_SIZE)

    if not players_batch:
        logger.warning("No players found in database to evaluate.")
        scraper.stop()
        return

    logger.info(
        "Loaded %d players from database. Running evaluation cycle...",
        len(players_batch),
    )

    bot_opportunities = []

    try:
        scraper.login(config.PM_USERNAME, config.PM_PASSWORD)

        for i, player in enumerate(players_batch):
            pid = player["id"]
            team_name = player.get("team_name", "Unknown")

            if i > 0 and i % 50 == 0:
                logger.info("Progress: %d / %d players evaluated", i, len(players_batch))

            try:
                result = scraper.evaluate_player(pid, team_name)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if result:
                    result["last_evaluated_at"] = timestamp
                    bot_opportunities.append(result)
                else:
                    # Player page returned no data — still bump the timestamp so
                    # this player doesn't block the evaluation queue.
                    bot_opportunities.append(
                        {
                            "id": pid,
                            "team_name": team_name,
                            "last_evaluated_at": timestamp,
                        }
                    )
            except Exception as e:
                logger.error("Error evaluating player %s: %s", pid, e)

    except Exception as e:
        logger.error("Global evaluation error: %s", e, exc_info=True)
    finally:
        scraper.stop()

    if not bot_opportunities:
        logger.warning("No players were evaluated successfully.")
        return

    df = pd.DataFrame(bot_opportunities)

    csv_file = "bot_evaluations_batch.csv"
    df.to_csv(csv_file, index=False)
    logger.info("Saved CSV backup to %s", csv_file)

    db.upsert_bot_opportunities(df.to_dict(orient="records"))


if __name__ == "__main__":
    main()
