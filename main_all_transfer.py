import os
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from scraper_all_transfer import AllTransferScraper
import gspread
from google.oauth2.service_account import Credentials

# Google Sheets Configuration
SPREADSHEET_ID = "1F8FWV9w1gNAGbGDd6RG929dx2jAcM-N6p2ve9fOwSfU"
SHEET_NAME = "All Players"

def upload_to_sheets(df, spreadsheet_id, sheet_name):
    """Upload DataFrame to Google Sheets (Upsert: Update existing, Add new)"""
    try:
        # Authenticate
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
        client = gspread.authorize(creds)
        
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            # Fetch existing data
            existing_records = worksheet.get_all_records()
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
            existing_records = []
            
        if existing_records:
            print(f"  Found {len(existing_records)} existing records. Merging...")
            df_old = pd.DataFrame(existing_records)
            
            # Ensure ID consistency (string)
            if 'id' in df_old.columns:
                df_old['id'] = df_old['id'].astype(str)
            if 'id' in df.columns:
                df['id'] = df['id'].astype(str)
                
            # Set ID as index
            df.set_index('id', inplace=True)
            df_old.set_index('id', inplace=True)
            
            # Upsert Logic:
            # 1. Take all rows from NEW df (this updates existing IDs with new data)
            # 2. Append rows from OLD df that are NOT in NEW df (preserves historical data)
            df_final = pd.concat([df, df_old[~df_old.index.isin(df.index)]])
            
            # Reset index to make 'id' a column again
            df_final.reset_index(inplace=True)
        else:
            print("  No existing data. Creating new sheet.")
            df_final = df

        # Clean up (Fill NaNs)
        df_final = df_final.fillna("")
        
        # Helper to sort columns cleanly (Optional, but good for UI)
        # Put 'id', 'name', 'position' first if they exist
        cols = list(df_final.columns)
        priority = ['id', 'name', 'position', 'age', 'team', 'Quality', 'Potential', 'last_updated']
        sorted_cols = [c for c in priority if c in cols] + [c for c in cols if c not in priority]
        df_final = df_final[sorted_cols]
        
        # Clear & Upload
        worksheet.clear()
        data = [df_final.columns.tolist()] + df_final.values.tolist()
        worksheet.update(data, value_input_option="USER_ENTERED")
        
        print(f"✓ Uploaded {len(df_final)} rows (Merged) to Google Sheets: {sheet_name}")
        return True
    except Exception as e:
        print(f"✗ Failed to upload to Google Sheets: {e}")
        return False

def main():
    load_dotenv()
    username = os.getenv("PM_USERNAME")
    password = os.getenv("PM_PASSWORD")

    if not username or not password:
        print("Error: PM_USERNAME and PM_PASSWORD must be set in .env file")
        return
    
    print("Starting All Transfer Players Scraper...")
    scraper = AllTransferScraper()
    
    try:
        # CI/Headless Check
        is_ci = os.getenv("CI", "false").lower() == "true"
        scraper.start(headless=is_ci)
        
        if username and password:
            scraper.login(username, password)
            
            # 1. Search (Get IDs)
            player_ids = scraper.search_transfer_list()
            
            # 2. Get Details for each
            results = []
            print(f"Extracting details for {len(player_ids)} players...")
            
            for i, pid in enumerate(player_ids):
                print(f"[{i+1}/{len(player_ids)}] Scraping ID: {pid}...", end="\r")
                try:
                    data = scraper.get_player_details(pid)
                    results.append(data)
                except Exception as e:
                    print(f"\nError scraping {pid}: {e}")
            
            print(f"\nSuccessfully scraped {len(results)} players.")
            
            if results:
                # 3. Save to CSV
                df = pd.DataFrame(results)
                
                # Timestamp
                thailand_time = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
                df["last_updated"] = thailand_time
                
                # Reorder columns to have generic info first
                cols = list(df.columns)
                priority_cols = ["id", "name", "position", "age", "team", "nationality", "Quality", "Potential", "url"]
                new_order = [c for c in priority_cols if c in cols] + [c for c in cols if c not in priority_cols]
                df = df[new_order]

                csv_file = "transfer_targets_all.csv"
                df.to_csv(csv_file, index=False)
                print(f"Saved results to {csv_file}")
                
                # 4. Upload to Google Sheets
                upload_to_sheets(df, SPREADSHEET_ID, SHEET_NAME)
            
        else:
            print("Credentials missing.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        scraper.stop()

if __name__ == "__main__":
    main()
