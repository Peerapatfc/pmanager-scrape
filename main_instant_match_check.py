"""One-shot check for open Instant Matches — alerts via Telegram.

Designed for GitHub Actions (stateless, no loop). Run on a cron schedule.
Alerts on every open Pending game found each run. Match ID in the alert
lets you identify duplicates across runs.

Usage:
    python main_instant_match_check.py
"""

from src.config import config
from src.core.logger import logger
from src.scrapers.instant_match import InstantMatchScraper
from src.services.telegram import TelegramBot


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
    config.validate_telegram()
    if not config.PM_USERNAME or not config.PM_PASSWORD:
        raise SystemExit("PM_USERNAME and PM_PASSWORD required")

    bot = TelegramBot()

    with InstantMatchScraper() as scraper:
        scraper.login(config.PM_USERNAME, config.PM_PASSWORD)
        matches = scraper.get_open_matches()

    if not matches:
        logger.info("No open instant matches found.")
        return

    logger.info("Sending %d alert(s)...", len(matches))
    for match in matches:
        msg = format_match_alert(match)
        bot.send_message(msg)
        logger.info("Alerted: match %s vs %s", match.match_id, match.team_name)


if __name__ == "__main__":
    main()
