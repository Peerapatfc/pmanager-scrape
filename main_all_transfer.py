import pandas as pd
import numpy as np
from datetime import datetime
from src.config import config
from src.core.logger import logger
from src.core.utils import clean_currency
from src.services.supabase_client import SupabaseManager
from src.scrapers.transfer import TransferScraper

def main():
    config.validate()
    
    # 1. Scrape Data
    scraper = TransferScraper(base_url="https://www.pmanager.org")
    scraper.start(headless=config.HEADLESS_MODE)
    
    all_results = []
    
    try:
        scraper.login(config.PM_USERNAME, config.PM_PASSWORD)
        
        logger.info("Starting 'All Players' Scrape...")
        player_ids = scraper.search_transfer_list(max_pages=150)
        
        for pid in player_ids:
            logger.info(f"Get details: {pid}")
            details = scraper.get_player_details(pid)
            
            # Post-processing / cleaning
            if "estimated_value" in details and "asking_price" in details:
                 est = details["estimated_value"]
                 ask = details["asking_price"]
                 details["value_diff"] = est - ask
                 if ask > 0:
                     details["roi"] = round(((est - ask) / ask) * 100, 2)
                 else:
                     details["roi"] = 0
                     
                 # Forecast Sell
                 details["forecast_sell"] = (est / 2) * 0.8
                 
                 # Forecast Profit
                 bids_avg = 0
                 if "bids_avg" in details:
                     bids_avg = clean_currency(str(details["bids_avg"]))
                 
                 cost_price = max(ask, bids_avg)
                 details["forecast_profit"] = details["forecast_sell"] - cost_price
            
            all_results.append(details)
            
    except Exception as e:
        logger.error(f"Global Scraper Error: {e}")
    finally:
        scraper.stop()

    if not all_results:
        logger.warning("No results found.")
        return

    # 2. Process Data
    df = pd.DataFrame(all_results)
    
    # Clean Data
    df.replace([np.inf, -np.inf], 0, inplace=True)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)
    
    # Save CSV (backup)
    csv_file = "transfer_targets_all.csv"
    df.to_csv(csv_file, index=False)
    logger.info(f"Saved CSV to {csv_file}")
    
    # 3. Upload to Supabase
    db = SupabaseManager()
    
    # Transfer Listings
    market_cols = ["id", "name", "position", "age", "Quality", "Potential", 
                   "estimated_value", "asking_price", "value_diff", "roi", 
                   "forecast_sell", "forecast_profit", "deadline", "url"]
    existing_mcols = [c for c in market_cols if c in df.columns]
    df_market = df[existing_mcols].copy()
    df_market['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    transfer_records = df_market.to_dict(orient="records")
    db.replace_transfer_listings(transfer_records)

    # All Players (Attributes)
    drop_cols = ["estimated_value", "asking_price", "buy_price", "value_diff", 
                 "roi", "bids_count", "forecast_sell"]
    attr_cols = [c for c in df.columns if c not in drop_cols]
    df_attributes = df[attr_cols].copy()
    
    player_records = df_attributes.to_dict(orient="records")
    db.upsert_players(player_records)

if __name__ == "__main__":
    main()
