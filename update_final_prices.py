from datetime import datetime, timedelta
from src.config import config
from src.core.logger import logger
from src.core.utils import parse_deadline, clean_currency
from src.services.gsheets import SheetManager
from src.scrapers.transfer import TransferScraper

def main():
    config.validate()
    
    logger.info("Starting Price Updater...")
    sheet_manager = SheetManager()
    
    records = sheet_manager.get_all_records(config.SHEET_NAME_ALL_PLAYERS)
    logger.info(f"Loaded {len(records)} players.")
    
    scraper = TransferScraper(base_url="https://www.pmanager.org")
    scraper.start(headless=config.HEADLESS_MODE)
    
    updates_count = 0
    # utils.parse_deadline returns TH time (UTC+7)
    # So we compare against current UTC+7
    now_th = datetime.utcnow() + timedelta(hours=7)
    
    try:
        scraper.login(config.PM_USERNAME, config.PM_PASSWORD)
        
        for i, row in enumerate(records):
            pid = str(row.get("id", ""))
            if not pid: continue
            
            deadline_str = str(row.get("deadline", ""))
            last_price = row.get("last_transfer_price", 0)
            
            # Use utility to parsing
            dead_dt = parse_deadline(deadline_str)
            
            if not dead_dt:
                continue
                
            diff = now_th - dead_dt
            diff_hours = diff.total_seconds() / 3600
            
            # PHASE 1: Active (Future)
            if diff_hours < 0:
                 # Active
                 # Check if we should update bids (optional, but good)
                 # Only if it's been a while? Or just verify logic from old script
                 pass 
                 # Original script had logic here to update active listings.
                 # Let's check logic:
                 # if dead_dt and diff_hours is not None and diff_hours < 0: ...
                 
                 logger.debug(f"Active: {pid}, ends in {-diff_hours:.1f}h")
                 # We can update active stats
                 try:
                     bid_info = scraper.get_bid_info(pid)
                     if bid_info["estimated_value"] > 0: records[i]["estimated_value"] = bid_info["estimated_value"]
                     records[i]["bids_count"] = bid_info["bids_count"]
                     if bid_info["bids_avg"]: records[i]["bids_avg"] = bid_info["bids_avg"]
                     if bid_info["deadline"] != "N/A": records[i]["deadline"] = bid_info["deadline"]
                     updates_count += 1
                 except: pass

            # PHASE 2: Completed (> 0h)
            # Check if recent and missing price
            elif diff_hours > 0: # Expired
                 # If we don't have price yet
                 if not last_price or str(last_price) == "0":
                      # If it expired recently (e.g. < 24h) to avoid checking 5 year old players
                      # Original: diff_hours > 2 (Wait 2 hours)
                      
                      if diff_hours > 2: # Wait for system to process
                           logger.info(f"Checking Final Price: {pid} (Expired {diff_hours:.1f}h ago)")
                           price = scraper.get_player_history(pid)
                           
                           if price > 0:
                                records[i]["last_transfer_price"] = price
                                
                                # Ratio
                                text_avg = str(row.get("bids_avg", "0"))
                                clean_avg = clean_currency(text_avg)
                                
                                if clean_avg > 0:
                                     records[i]["sale_to_bid_ratio"] = round(price / clean_avg, 2)
                                else:
                                     records[i]["sale_to_bid_ratio"] = 0
                                
                                updates_count += 1
                                logger.info(f"  -> Sold: {price}")
                           else:
                                logger.debug("  -> No transfer found.")

    except Exception as e:
        logger.error(f"Updater Error: {e}")
    finally:
        scraper.stop()
        
    if updates_count > 0:
        logger.info(f"Updating {updates_count} rows...")
        # Prepare headers
        if records:
            headers = list(records[0].keys())
            data = [headers] + [[r.get(h, "") for h in headers] for r in records]
            sheet_manager.upload_data(config.SHEET_NAME_ALL_PLAYERS, data, clear=True)
    else:
        logger.info("No updates needed.")

if __name__ == "__main__":
    main()
