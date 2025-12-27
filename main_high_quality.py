import os
from datetime import datetime
from dotenv import load_dotenv
from scraper_high_quality import PMScraper
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# Google Sheets Configuration
SPREADSHEET_ID = "1F8FWV9w1gNAGbGDd6RG929dx2jAcM-N6p2ve9fOwSfU"
SHEET_NAME = "High Quality"  # Sheet tab name

def upload_to_sheets(df, spreadsheet_id, sheet_name):
    """Upload DataFrame to Google Sheets"""
    try:
        # Authenticate with Google Sheets
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
        client = gspread.authorize(creds)
        
        # Open spreadsheet and worksheet
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        # Try to get existing worksheet or create new one
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            worksheet.clear()  # Clear existing data
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
        
        # Upload data (header + rows)
        data = [df.columns.tolist()] + df.values.tolist()
        worksheet.update(data, value_input_option="USER_ENTERED")
        
        print(f"✓ Uploaded {len(df)} rows to Google Sheets: {sheet_name}")
        return True
    except Exception as e:
        print(f"✗ Failed to upload to Google Sheets: {e}")
        return False

def parse_bids_avg(bids_avg_str):
    """Parse bids_avg string to numeric value. Returns 0 if parsing fails."""
    if not bids_avg_str or bids_avg_str == "-":
        return 0
    try:
        # Remove 'baht' and clean up the string (handle formats like "23.133.150 baht")
        cleaned = str(bids_avg_str).replace(" baht", "").replace("baht", "").strip()
        # Handle European/Thai format where . is thousands separator
        cleaned = cleaned.replace(".", "")
        return int(cleaned)
    except (ValueError, AttributeError):
        return 0


def main():
    load_dotenv()
    username = os.getenv("PM_USERNAME")
    password = os.getenv("PM_PASSWORD")

    if not username or not password:
        print("Error: PM_USERNAME and PM_PASSWORD must be set in .env file")
        # We'll continue for now since we might just be testing the setup
    
    print("Starting High Quality scraper...")
    scraper = PMScraper()
    try:
        # Use headless mode in CI environment (GitHub Actions)
        is_ci = os.getenv("CI", "false").lower() == "true"
        scraper.start(headless=is_ci) 
        if username and password and username != "your_username":
            scraper.login(username, password)
            
            # 1. Search for players
            player_ids = scraper.search_transfer_list()
            
            # 2. Extract Estimated Transfer Value for each
            results = []
            print(f"Extracting data for {len(player_ids)} players...")
            
            for i, pid in enumerate(player_ids):
                data = scraper.get_estimated_value(pid)
                est_val = data["estimated_value"]
                ask_price = data["asking_price"]
                bids_avg_num = parse_bids_avg(data["bids_avg"])
                
                # Calculate Value Difference and ROI (using max of asking_price and bids_avg)
                buy_price = max(ask_price, bids_avg_num)
                value_diff = est_val - buy_price
                roi = (value_diff / buy_price * 100) if buy_price > 0 else 0
                data["buy_price"] = buy_price
                data["value_diff"] = value_diff
                data["roi"] = round(roi, 2)

                print(f"[{i+1}/{len(player_ids)}] ID: {pid} | Est: {est_val:,} | Buy: {buy_price:,} | Diff: {value_diff:,} | ROI: {roi:.1f}%")
                results.append(data)
                
            # 3. Sort by ROI (Descending)
            results.sort(key=lambda x: x["roi"], reverse=True)
            
            # 4. List Top 5
            print("\n" + "="*70)
            print("TOP 5 PLAYERS BY ROI (Return on Investment)")
            print("="*70)
            
            for i, p in enumerate(results[:5]):
                print(f"{i+1}. Player ID: {p['id']}")
                print(f"   ROI: {p['roi']:.2f}%")
                print(f"   Est. Value: {p['estimated_value']:,} baht")
                print(f"   Asking Price: {p['asking_price']:,} baht")
                print(f"   Value Diff: {p['value_diff']:,} baht")
                print(f"   Deadline: {p['deadline']}")
                print(f"   Bids: {p['bids_count']} | Avg: {p['bids_avg']}")
                print(f"   Link: https://www.pmanager.org/ver_jogador.asp?jog_id={p['id']}")
                print("-" * 70)
                
            # Optional: Save to CSV
            df = pd.DataFrame(results)
            
            # Add Last Updated Timestamp (Thailand Time = UTC+7)
            from datetime import timedelta
            thailand_time = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
            df["last_updated"] = thailand_time
            
            df.to_csv("transfer_targets_high_quality.csv", index=False)
            print("Saved all results to transfer_targets_high_quality.csv")
            
            # Format currency columns for Google Sheets
            df_formatted = df.copy()
            df_formatted["estimated_value"] = df_formatted["estimated_value"].apply(lambda x: f"฿ {x:,.0f}")
            df_formatted["asking_price"] = df_formatted["asking_price"].apply(lambda x: f"฿ {x:,.0f}")
            df_formatted["buy_price"] = df_formatted["buy_price"].apply(lambda x: f"฿ {x:,.0f}")
            df_formatted["value_diff"] = df_formatted["value_diff"].apply(lambda x: f"฿ {x:,.0f}")
            
            # Upload to Google Sheets
            upload_to_sheets(df_formatted, SPREADSHEET_ID, SHEET_NAME)
            
        else:
            print("Skipping login (no credentials or default credentials)")
            print("Please update .env with actual credentials.")
 

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        scraper.stop()

if __name__ == "__main__":
    main()
