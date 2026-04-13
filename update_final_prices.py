"""
Final price updater entry point.

Runs hourly to keep player data in Supabase fresh:

- **Active listings** (deadline in the future): refreshes bid count, bid
  average, and estimated value from the negotiation page.
- **Completed listings** (deadline passed by ≥
  :data:`~src.constants.FINAL_PRICE_GRACE_HOURS` hours): fetches the final
  sale price from the player's transfer history and calculates the
  sale-to-bid ratio.

Usage::

    python update_final_prices.py
"""

from datetime import datetime, timedelta

from src import constants
from src.config import config
from src.core.logger import logger
from src.core.utils import clean_currency, parse_deadline
from src.scrapers.transfer import TransferScraper
from src.services.supabase_client import SupabaseManager


def main() -> None:
    """Update active and recently-completed player listings in Supabase."""
    config.validate()

    logger.info("Starting Price Updater...")
    db = SupabaseManager()

    records = db.get_players_for_price_update()
    logger.info("Loaded %d players for price update.", len(records))

    scraper = TransferScraper(base_url="https://www.pmanager.org")
    scraper.start(headless=config.HEADLESS_MODE)

    updates_count = 0
    now_th = datetime.utcnow() + timedelta(hours=constants.UTC_OFFSET_HOURS)

    try:
        scraper.login(config.PM_USERNAME, config.PM_PASSWORD)

        for row in records:
            pid = str(row.get("id", ""))
            if not pid:
                continue

            deadline_str = str(row.get("deadline", ""))
            last_price = row.get("last_transfer_price", 0)

            dead_dt = parse_deadline(deadline_str)
            if not dead_dt:
                continue

            diff = now_th - dead_dt
            diff_hours = diff.total_seconds() / 3600

            # --- Active listing (deadline still in the future) ---
            if diff_hours < 0:
                logger.debug("Active: %s, ends in %.1fh", pid, -diff_hours)
                try:
                    bid_info = scraper.get_bid_info(pid)
                    update_data = {}
                    if bid_info["estimated_value"] > 0:
                        update_data["estimated_value"] = bid_info["estimated_value"]
                    if bid_info["bids_count"]:
                        update_data["bids_count"] = str(bid_info["bids_count"])
                    if bid_info["bids_avg"]:
                        update_data["bids_avg"] = bid_info["bids_avg"]
                    if bid_info["deadline"] != "N/A":
                        update_data["deadline"] = bid_info["deadline"]

                    if update_data:
                        db.update_player(pid, update_data)
                        updates_count += 1
                except Exception as e:
                    logger.debug("Error updating active player %s: %s", pid, e)

            # --- Completed listing (enough time has passed to record sale price) ---
            elif diff_hours > constants.FINAL_PRICE_GRACE_HOURS:
                if not last_price or str(last_price) == "0":
                    logger.info(
                        "Checking final price: %s (expired %.1fh ago)", pid, diff_hours
                    )
                    price = scraper.get_player_history(pid)

                    if price > 0:
                        update_data = {"last_transfer_price": price}

                        clean_avg = clean_currency(str(row.get("bids_avg", "0")))
                        update_data["sale_to_bid_ratio"] = (
                            round(price / clean_avg, 2) if clean_avg > 0 else 0
                        )

                        db.update_player(pid, update_data)
                        updates_count += 1
                        logger.info("  -> Sold: %s", price)
                    else:
                        logger.debug("  -> No transfer found for %s.", pid)

    except Exception as e:
        logger.error("Updater error: %s", e, exc_info=True)
    finally:
        scraper.stop()

    logger.info("Updated %d players in Supabase.", updates_count)


if __name__ == "__main__":
    main()
