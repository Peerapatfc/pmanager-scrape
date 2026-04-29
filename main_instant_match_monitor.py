"""Monitor the PManager Instant Match lobby and alert via Telegram.

Polls pvp_geral.asp every POLL_INTERVAL seconds. Sends a Telegram alert
for each new open (Pending, no opponent) game. Skips already-seen match IDs.

Usage:
    python main_instant_match_monitor.py
"""

import time

from src.config import config
from src.core.logger import logger
from src.scrapers.instant_match import InstantMatchScraper
from src.services.telegram import TelegramBot

POLL_INTERVAL = 30  # seconds between checks


def format_match_alert(match) -> str:
    lines = [
        "⚡ *Instant Match Open!*",
        f"🆔 Match ID: `{match.match_id}`",
        f"🏟 Opponent: *{match.team_name}*",
    ]
    if match.division_title:
        lines.append(f"🏆 Division: {match.division_title}")
    lines.append(f"🕐 Time: {match.time}")
    lines.append(f"🌤 Weather: {match.weather}")
    lines.append(f"🔗 [Join Now](https://www.pmanager.org/pvp_geral.asp)")
    return "\n".join(lines)


def main() -> None:
    config.validate()

    bot = TelegramBot()
    seen_ids: set[str] = set()

    logger.info("Instant match monitor started. Poll interval: %ds", POLL_INTERVAL)

    with InstantMatchScraper() as scraper:
        scraper.login(config.PM_USERNAME, config.PM_PASSWORD)

        while True:
            try:
                matches = scraper.get_open_matches()
                new_matches = [m for m in matches if m.match_id not in seen_ids]

                for match in new_matches:
                    msg = format_match_alert(match)
                    if bot.send_message(msg):
                        seen_ids.add(match.match_id)
                        logger.info("Alerted: match %s vs %s", match.match_id, match.team_name)
                    else:
                        logger.warning("Failed to send alert for match %s", match.match_id)

                if not new_matches:
                    logger.info("No new open matches. Sleeping %ds...", POLL_INTERVAL)

            except Exception as e:
                logger.error("Poll error: %s", e, exc_info=True)

            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
