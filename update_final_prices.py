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
    
    # Base is UTC (system time often UTC in CI, but here we run locally or cloud)
    # The site times are often relative.
    # We assume "Today" = Current UTC Date, then converted.
    # Actually site is UTC usually?
    # Let's align with ai_recommendation logic:
    # "Base is UTC... Convert to Thailand Time (UTC+7)"
    
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
    
    # 2. Identify Targets
    # Check if deadline passed within the last X hours (e.g. 2 hours to be safe)
    # And last_transfer_price is 0 or empty
    
    targets = []
    
    # We need row index to update specifically? 
    # gspread batch update is better. We can reconstruct the whole data or update cells.
    # Since we might update random rows, updating cells is better or re-uploading all.
    # Re-uploading all is easier but risks overwriting if other processes run.
    # But usually this is the only writer to 'All Players' attributes except main scraper.
    # Let's modify 'records' in place and re-upload.
    
    updates_count = 0
    
    scraper = AllTransferScraper()
    scraper.start(headless=True)
    
    # Login (Might be needed for history page?)
    # History page is usually public? "marcos_jog.asp" might be public.
    # Let's try without login first? No, usually PManager requires login for details.
    username = os.getenv("PM_USERNAME")
    password = os.getenv("PM_PASSWORD")
    if username and password:
        scraper.login(username, password)
    
    try:
        for i, row in enumerate(records):
            pid = str(row.get("id", ""))
            deadline_str = str(row.get("deadline", ""))
            last_price = row.get("last_transfer_price", 0)
            
            # Skip if already has price (assuming > 0 means we got it)
            # Note: Sometimes it sold for 0? Unlikely.
            if last_price and str(last_price) != "0" and str(last_price) != "":
                continue
                
            if not pid: continue
            
            dead_dt = parse_deadline(deadline_str)
            if not dead_dt: continue
            
            # Check deviation
            # We want: Deadline < Now (It passed)
            # And: Now - Deadline <= 2 hours (It passed recently)
            diff = now_th - dead_dt
            diff_hours = diff.total_seconds() / 3600
            
            # If diff positive, deadline passed.
            # We look for window: 0 < diff_hours < 2
            # Or maybe just "passed and we don't have price"?
            # User said "get player only pass deadline within hour".
            
            if 0 < diff_hours <= 2: 
                print(f"Target found: {row.get('name')} (ID: {pid}) | Ended {diff_hours:.1f}h ago")
                
                # Scrape
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
        # We replace the whole sheet to be simple and safe with indices
        # Ensure headers match
        headers = list(records[0].keys())
        # We need to make sure 'last_transfer_price' is a column. 
        # get_all_records uses first row as keys.
        
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
