from datetime import datetime, timedelta
from src.config import config
from src.core.logger import logger
from src.core.utils import parse_deadline, clean_currency
from src.services.supabase_client import SupabaseManager
from src.scrapers.transfer import TransferScraper

def main():
    config.validate()
    
    logger.info("Starting Price Updater...")
    db = SupabaseManager()
    
    records = db.get_all_players()
    logger.info(f"Loaded {len(records)} players.")
    
    scraper = TransferScraper(base_url="https://www.pmanager.org")
    scraper.start(headless=config.HEADLESS_MODE)
    
    updates_count = 0
    now_th = datetime.utcnow() + timedelta(hours=7)
    
    try:
        scraper.login(config.PM_USERNAME, config.PM_PASSWORD)
        
        for row in records:
            pid = str(row.get("id", ""))
            if not pid: continue
            
            deadline_str = str(row.get("deadline", ""))
            last_price = row.get("last_transfer_price", 0)
            
            dead_dt = parse_deadline(deadline_str)
            
            if not dead_dt:
                continue
                
            diff = now_th - dead_dt
            diff_hours = diff.total_seconds() / 3600
            
            # PHASE 1: Active (Future)
            if diff_hours < 0:
                 logger.debug(f"Active: {pid}, ends in {-diff_hours:.1f}h")
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
                 except: pass

            # PHASE 2: Completed (> 0h)
            elif diff_hours > 0:
                 if not last_price or str(last_price) == "0":
                      if diff_hours > 2:
                           logger.info(f"Checking Final Price: {pid} (Expired {diff_hours:.1f}h ago)")
                           price = scraper.get_player_history(pid)
                           
                           if price > 0:
                                update_data = {"last_transfer_price": price}
                                
                                text_avg = str(row.get("bids_avg", "0"))
                                clean_avg = clean_currency(text_avg)
                                
                                if clean_avg > 0:
                                     update_data["sale_to_bid_ratio"] = round(price / clean_avg, 2)
                                else:
                                     update_data["sale_to_bid_ratio"] = 0
                                
                                db.update_player(pid, update_data)
                                updates_count += 1
                                logger.info(f"  -> Sold: {price}")
                           else:
                                logger.debug("  -> No transfer found.")

    except Exception as e:
        logger.error(f"Updater Error: {e}")
    finally:
        scraper.stop()
        
    logger.info(f"Updated {updates_count} players in Supabase.")

if __name__ == "__main__":
    main()
