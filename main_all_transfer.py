"""
Transfer market scraper entry point.

Scrapes the full PManager transfer market, calculates ROI and profit
metrics for each listing, then uploads the results to Supabase:

- ``transfer_listings`` table: all current market opportunities.
- ``players`` table: player attributes upserted from the same run.

A CSV backup is also written to ``transfer_targets_all.csv``.

Usage::

    python main_all_transfer.py
"""

from datetime import datetime

import numpy as np
import pandas as pd

from src import constants
from src.config import config
from src.core.logger import logger
from src.core.utils import clean_currency
from src.scrapers.transfer import TransferScraper
from src.services.supabase_client import SupabaseManager


def main() -> None:
    """Run the full transfer market scrape and upload results to Supabase."""
    config.validate()

    scraper = TransferScraper(base_url="https://www.pmanager.org")
    scraper.start(headless=config.HEADLESS_MODE)

    all_results = []

    try:
        scraper.login(config.PM_USERNAME, config.PM_PASSWORD)

        logger.info("Starting 'All Players' Scrape...")
        player_ids = scraper.search_transfer_list(max_pages=150)

        for pid in player_ids:
            logger.info("Get details: %s", pid)
            try:
                details = scraper.get_player_details(pid)
            except Exception as e:
                logger.error("Failed to get details for player %s: %s", pid, e)
                continue

            # Calculate market metrics
            if "estimated_value" in details and "asking_price" in details:
                est = details["estimated_value"]
                ask = details["asking_price"]
                details["value_diff"] = est - ask

                if ask > 0:
                    details["roi"] = round(((est - ask) / ask) * 100, 2)
                else:
                    details["roi"] = 0

                # Conservative resale forecast:
                #   forecast_sell = (estimated_value / DIVISOR) * MULTIPLIER
                details["forecast_sell"] = (
                    (est / constants.FORECAST_SELL_DIVISOR) * constants.FORECAST_SELL_MULTIPLIER
                )

                bids_avg = 0.0
                if "bids_avg" in details:
                    bids_avg = clean_currency(str(details["bids_avg"]))

                cost_price = max(ask, bids_avg)
                details["forecast_profit"] = details["forecast_sell"] - cost_price

            all_results.append(details)

    except Exception as e:
        logger.error("Global scraper error: %s", e, exc_info=True)
    finally:
        scraper.stop()

    if not all_results:
        logger.warning("No results found.")
        return

    # Process data
    df = pd.DataFrame(all_results)
    df.replace([np.inf, -np.inf], 0, inplace=True)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)

    # Save CSV backup
    csv_file = "transfer_targets_all.csv"
    df.to_csv(csv_file, index=False)
    logger.info("Saved CSV to %s", csv_file)

    # Upload to Supabase
    db = SupabaseManager()

    # Transfer listings
    market_cols = [
        "id", "name", "position", "age", "Quality", "Potential",
        "estimated_value", "asking_price", "value_diff", "roi",
        "forecast_sell", "forecast_profit", "deadline", "url",
    ]
    existing_mcols = [c for c in market_cols if c in df.columns]
    df_market = df[existing_mcols].copy()
    df_market["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    db.replace_transfer_listings(df_market.to_dict(orient="records"))

    # All players (attributes only — no financial columns)
    drop_cols = [
        "estimated_value", "asking_price", "buy_price", "value_diff",
        "roi", "bids_count", "forecast_sell",
    ]
    attr_cols = [c for c in df.columns if c not in drop_cols]
    db.upsert_players(df[attr_cols].to_dict(orient="records"))


if __name__ == "__main__":
    main()
