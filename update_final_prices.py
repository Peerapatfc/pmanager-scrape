import os
import re
import time
import gspread
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from scraper_all_transfer import AllTransferScraper

# Configuration
SPREADSHEET_ID = "1F8FWV9w1gNAGbGDd6RG929dx2jAcM-N6p2ve9fOwSfU"
SHEET_NAME = "All Players"

def get_sheet_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
    return gspread.authorize(creds)

def parse_deadline(deadline_str):
    """
    Parse 'Today at 10:19' or 'Tomorrow at ...' -> UTC+7 Datetime
    Same logic as ai_recommendation.py
    """
    if not deadline_str or not isinstance(deadline_str, str):
        return None
    
    txt = deadline_str.lower().strip()
    match = re.search(r'(\d{1,2}):(\d{2})', txt)
    if not match:
        return None
        
    hour = int(match.group(1))
    minute = int(match.group(2))
    
    utc_now = datetime.utcnow()
    
    if "today" in txt:
        target_utc = utc_now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    elif "tomorrow" in txt:
        target_utc = (utc_now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
    else:
        # Might be a date like "12/01 ..." if far future, but usually scraper sees relative
        return None
    
    # Return TH time for consistency with "now_th"
    return target_utc + timedelta(hours=7)

def main():
    load_dotenv()
    
    # 1. Setup
    print("Connecting to Google Sheets...")
    client = get_sheet_client()
    sh = client.open_by_key(SPREADSHEET_ID)
    worksheet = sh.worksheet(SHEET_NAME)
    
    # Get all records
    records = worksheet.get_all_records()
    print(f"Loaded {len(records)} players from '{SHEET_NAME}'.")
    
    # Current Time (TH)
    now_th = datetime.utcnow() + timedelta(hours=7)
    print(f"Current Time (TH): {now_th.strftime('%Y-%m-%d %H:%M')}")
    
    updates_count = 0
    
    scraper = AllTransferScraper()
    scraper.start(headless=True)
    
    # Login
    username = os.getenv("PM_USERNAME")
    password = os.getenv("PM_PASSWORD")
    if username and password:
        scraper.login(username, password)
    
    try:
        for i, row in enumerate(records):
            pid = str(row.get("id", ""))
            if not pid:
                continue
                
            deadline_str = str(row.get("deadline", ""))
            last_price = row.get("last_transfer_price", 0)
            
            dead_dt = parse_deadline(deadline_str)
            
            # Calculate time difference
            if dead_dt:
                diff = now_th - dead_dt
                diff_hours = diff.total_seconds() / 3600
            else:
                diff_hours = None
            
            # =====================================================
            # PHASE 1: Active Listings (deadline NOT passed yet)
            # Update: estimated_value, bids_count, bids_avg, deadline
            # =====================================================
            if dead_dt and diff_hours is not None and diff_hours < 0:
                # Deadline is in the future = still active
                print(f"Active listing: {row.get('name')} (ID: {pid}) | Ends in {-diff_hours:.1f}h")
                
                try:
                    bid_info = scraper.get_bid_info(pid)
                    
                    # Update fields
                    if bid_info.get("estimated_value", 0) > 0:
                        records[i]["estimated_value"] = bid_info["estimated_value"]
                    if bid_info.get("bids_count", "0") != "0":
                        records[i]["bids_count"] = bid_info["bids_count"]
                    if bid_info.get("bids_avg", "N/A") != "N/A":
                        records[i]["bids_avg"] = bid_info["bids_avg"]
                    if bid_info.get("deadline", "N/A") != "N/A":
                        records[i]["deadline"] = bid_info["deadline"]
                    
                    updates_count += 1
                    print(f"  -> Updated: est={bid_info.get('estimated_value', 0):,}, bids={bid_info.get('bids_count', '0')}, avg={bid_info.get('bids_avg', 'N/A')}")
                    
                except Exception as e:
                    print(f"  -> Error: {e}")
            
            # =====================================================
            # PHASE 2: Completed Listings (deadline passed > 2 hours)
            # Update: last_transfer_price from history
            # =====================================================
            elif dead_dt and diff_hours is not None and diff_hours > 2:
                # Skip if already has price
                if last_price and str(last_price) != "0" and str(last_price) != "":
                    continue
                
                print(f"Completed listing: {row.get('name')} (ID: {pid}) | Ended {diff_hours:.1f}h ago")
                
                try:
                    price = scraper.get_player_history(pid)
                    if price > 0:
                        records[i]["last_transfer_price"] = price
                        updates_count += 1
                        print(f"  -> Sold for: {price:,}")
                    else:
                        print("  -> No transfer recorded yet.")
                except Exception as e:
                    print(f"  -> Error: {e}")
                    
    finally:
        scraper.stop()
        
    # 3. Save Updates
    if updates_count > 0:
        print(f"Updating {updates_count} records in sheet...")
        headers = list(records[0].keys())
        
        # Prepare data list
        data_to_upload = [headers]
        for r in records:
            data_to_upload.append([r.get(h, "") for h in headers])
            
        worksheet.update(data_to_upload, value_input_option="USER_ENTERED")
        print("Update complete.")
    else:
        print("No updates needed.")

if __name__ == "__main__":
    main()
