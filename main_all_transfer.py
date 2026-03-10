import pandas as pd
import numpy as np
from datetime import datetime
from src.config import config
from src.core.logger import logger
from src.core.utils import clean_currency
from src.services.gsheets import SheetManager
from src.scrapers.transfer import TransferScraper

def main():
    config.validate()
    
    # 1. Scrape Data
    scraper = TransferScraper(base_url="https://www.pmanager.org")
    scraper.start(headless=config.HEADLESS_MODE)
    
    all_results = []
    
    try:
        scraper.login(config.PM_USERNAME, config.PM_PASSWORD)
        
        # Scenario: "All Players" (or custom scenarios could be added here loop)
        logger.info("Starting 'All Players' Scrape...")
        player_ids = scraper.search_transfer_list(max_pages=150) # Use 150 as default
        
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
                 # profit = forecast_sell - cost_price
                 # cost_price = max(asking_price, bids_avg)
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
    
    # Clean Data before any usage (Fix JSON compliance issues)
    # Replace Infinity with 0
    df.replace([np.inf, -np.inf], 0, inplace=True)
    # Fill NaN with 0 for numeric/general safety before JSON serialization
    # Ideally, we should apply this selectively, but for this scraper 0 is safe for missing metrics.
    # However, strings might need "", let's be careful.
    # For now, let's fillna(0) for calculations, but let's do it on specific numeric cols if possible.
    # Or just handle it at export.
    # The error "Out of range float values" is strictly Inf/NaN in floats.
    
    # Explicitly handle numeric columns regarding NaN/Inf again to be sure
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)
    
    # Save CSV
    csv_file = "transfer_targets_all.csv"
    df.to_csv(csv_file, index=False)
    logger.info(f"Saved CSV to {csv_file}")
    
    # 3. Upload to Google Sheets
    sheet_manager = SheetManager()
    
    # Sheet 1: All Players (Upsert logic is complex with pure GSpread append, 
    # but for simplicity we will fetch existing, update, and push back, 
    # or just push 'Attributes'. The original logic filtered cols.)
    
    drop_cols = ["estimated_value", "asking_price", "buy_price", "value_diff", 
                 "roi", "bids_count", "forecast_sell"]
    # We KEEP bids_avg now as per recent requirements
    
    attr_cols = [c for c in df.columns if c not in drop_cols]
    df_attributes = df[attr_cols].copy()
    
    # Upsert Logic (Simplified: Read all, update matching IDs, append new)
    # Ideally checking existence.
    # For now, let's stick to the previous implementation's style if possible, 
    # OR since we refactored, let's do it cleaner: 
    # Just upload to "Transfer Info" fully first.
    
    # Transfer Info Upload
    market_cols = ["id", "name", "position", "age", "Quality", "Potential", 
                   "estimated_value", "asking_price", "value_diff", "roi", 
                   "forecast_sell", "forecast_profit", "deadline", "url"]
                   
    # Ensure cols exist
    existing_mcols = [c for c in market_cols if c in df.columns]
    df_market = df[existing_mcols].copy()
    df_market['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # CLEAN BEFORE UPLOAD (JSON compliance)
    df_market = df_market.fillna("") # Fill NaN with empty string for display/upload
    
    sheet_manager.upload_data(config.SHEET_NAME_TRANSFER_INFO, 
                              df_market.values.tolist(), 
                              columns=df_market.columns.tolist())

    # All Players (Attributes) Upload
    # To do a proper upsert without wiping history (like last_transfer_price),
    # we should read the existing sheet.
    
    try:
        existing_records = sheet_manager.get_all_records(config.SHEET_NAME_ALL_PLAYERS)
        existing_df = pd.DataFrame(existing_records)
        if not existing_df.empty:
             # Ensure 'id' is string in both to prevent "Invalid value for dtype 'str'"
             # existing_df might have IDs as ints if they look like numbers.
             existing_df['id'] = existing_df['id'].astype(str)
             
             # Clean df_attributes 'id'
             df_attributes['id'] = df_attributes['id'].fillna("").astype(str)
             # Filter out any empty IDs just in case
             df_attributes = df_attributes[df_attributes['id'] != ""]
             
             # Set index to ID for easy update
             existing_df.set_index('id', inplace=True)
             df_attributes.set_index('id', inplace=True)
             
             # Update existing with new values
             # Note: df_attributes might still have NaNs if we didn't fill them globally
             # Let's fill NaNs before updating to ensure we don't overwrite existing valid data with NaNs if that's undesired, 
             # OR if we want to overwrite, we must ensure they are not float NaNs which pandas might issue on.
             # However, update() usually works fine with NaNs (it ignores them), 
             # bUT if the new data has explicit None/NaN from scrape, we might want to overwrite.
             # Assuming scrape is authoritative for current state.
             
             # To solve "Invalid value for dtype 'str'": 
             # It usually happens if we try to put a float/int into a string-only column during combine/update or vice versa.
             # We should probably force everything to object or string if we are unsure.
             # But let's try just ensuring the update data is clean.
             df_attributes = df_attributes.fillna("") 
             
             existing_df.update(df_attributes)
             
             # Combine (this adds new rows that weren't in existing)
             # Note: update() only updates intersecting keys. 
             # We need to handle new rows.
             combined = df_attributes.combine_first(existing_df)
             
             # Reset index to upload
             df_final = combined.reset_index()
        else:
             df_final = df_attributes
             df_final['id'] = df_final['id'].astype(str) # Ensure string

        # Ensure 'sale_to_bid_ratio' and 'last_transfer_price' are preserved if they existed
        # combine_first should handle it if columns existed in existing_df
        
        # Sort by updated?
        # Clean again for JSON compliance before upload
        df_final = df_final.fillna("")
        df_final = df_final.replace([np.inf, -np.inf], 0)
        
        # Convert numpy types to native Python types to avoid
        # "Invalid value for dtype 'int64'" errors from Sheets API.
        # combine_first can produce numpy scalars that serialize badly.
        for col in df_final.columns:
            df_final[col] = df_final[col].apply(
                lambda x: int(x) if isinstance(x, (np.integer,)) 
                else float(x) if isinstance(x, (np.floating,)) 
                else x
            )
        
        sheet_manager.upload_data(config.SHEET_NAME_ALL_PLAYERS, 
                                  df_final.values.tolist(), 
                                  columns=df_final.columns.tolist())
                                  
    except Exception as e:
        logger.error(f"Error updating All Players sheet: {e}")

if __name__ == "__main__":
    main()
