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
            
            # 1. Search (Get IDs from Multiple Scenarios)
            all_found_ids = set()
            
            # Define Search Scenarios (Consolidated from legacy scrapers)
            SCENARIOS = [
                {
                    "name": "High Quality",
                    "url": "https://www.pmanager.org/procurar.asp?action=proc_jog&nome=&pos=0&nacional=-1&lado=-1&idd_op=%3C&idd=31&temp_op=%3C&temp=Any&expe_op=%3E%3D&expe=Any&con_op=%3C&con=Any&pro_op=%3E&pro=Any&vel_op=%3E&vel=Any&forma_op=%3E&forma=Any&cab_op=%3E&cab=Any&ord_op=%3C%3D&ord=Any&cul_op=%3E&cul=Any&pre_op=%3E&pre=Any&forca_op=%3E&forca=Any&lesionado=Any&prog_op=%3E&prog=Any&tack_op=%3E&tack=Any&internacional=Any&passe_op=%3E&passe=Any&pais=-1&rem_op=%3E&rem=Any&tec_op=%3E&tec=Any&jmaos_op=%3E&jmaos=Any&saidas_op=%3E&saidas=Any&reflexos_op=%3E&reflexos=Any&agilidade_op=%3E&agilidade=Any&B1=Pesquisar&field=&pid=1&sort=0&pv=1&qual_op=%3E&qual=7&talento=Any"
                },
                {
                    "name": "Low Price",
                    "url": "https://www.pmanager.org/procurar.asp?action=proc_jog&nome=&pos=0&nacional=-1&lado=-1&idd_op=%3C&idd=31&temp_op=%3C&temp=Any&expe_op=%3E%3D&expe=Any&con_op=%3C&con=Any&pro_op=%3E&pro=Any&vel_op=%3E&vel=Any&forma_op=%3E&forma=Any&cab_op=%3E&cab=Any&ord_op=%3C%3D&ord=Any&cul_op=%3E&cul=Any&pre_op=%3C%3D&pre=20000&forca_op=%3E&forca=Any&lesionado=Any&prog_op=%3E&prog=Any&tack_op=%3E&tack=Any&internacional=Any&passe_op=%3E&passe=Any&pais=-1&rem_op=%3E&rem=Any&tec_op=%3E&tec=Any&jmaos_op=%3E&jmaos=Any&saidas_op=%3E&saidas=Any&reflexos_op=%3E&reflexos=Any&agilidade_op=%3E&agilidade=Any&B1=Pesquisar&field=&pid=1&sort=0&pv=1&qual_op=%3E&qual=7&talento=Any"
                },
                {
                    "name": "Young Potential",
                    "url": "https://www.pmanager.org/procurar.asp?action=proc_jog&nome=&pos=0&nacional=-1&lado=-1&idd_op=%3C&idd=20&temp_op=%3C&temp=Any&expe_op=%3E%3D&expe=Any&con_op=%3C&con=Any&pro_op=%3E&pro=Any&vel_op=%3E&vel=Any&forma_op=%3E&forma=Any&cab_op=%3E&cab=Any&ord_op=%3C%3D&ord=Any&cul_op=%3E&cul=Any&pre_op=%3C%3D&pre=Any&forca_op=%3E&forca=Any&lesionado=Any&prog_op=%3E&prog=6&tack_op=%3E&tack=Any&internacional=Any&passe_op=%3E&passe=Any&pais=-1&rem_op=%3E&rem=Any&tec_op=%3E&tec=Any&jmaos_op=%3E&jmaos=Any&saidas_op=%3E&saidas=Any&reflexos_op=%3E&reflexos=Any&agilidade_op=%3E&agilidade=Any&B1=Pesquisar&field=&pid=1&sort=0&pv=1&qual_op=%3E&qual=Any&talento=Any"
                },
                {
                    "name": "Recent Listings (General)",
                    "url": None # Uses default URL
                }
            ]

            print(f"Running {len(SCENARIOS)} search scenarios...")
            
            for scenario in SCENARIOS:
                print(f"\n--- Scenario: {scenario['name']} ---")
                ids = scraper.search_transfer_list(search_url=scenario['url'])
                all_found_ids.update(ids)
                
            player_ids = list(all_found_ids)
            print(f"\nTotal Unique Players found from all scenarios: {len(player_ids)}")
            
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
            
            print(f"\nSuccessfully scraped {len(results)} players. Calculating values...")
            
            # --- CALCULATE VALUE METRICS ---
            for p in results:
                # 1. Parse numbers (remove commas if any, though scraper returns ints usually)
                try:
                    est = int(p.get("estimated_value", 0))
                    ask = int(p.get("asking_price", 0))
                    
                    # Scout Average - handle formatting like "10,000" or "N/A"
                    bid_avg_str = str(p.get("bids_avg", "0")).replace(",", "")
                    if bid_avg_str.isdigit():
                        bid_avg = int(bid_avg_str)
                    else:
                        bid_avg = 0
                        
                    # Buy Price is the max of Asking Price or Current average bid (roughly)
                    # Actually, if Asking Price is set, that's often the immediate buy or min bid. 
                    # Let's assume Buy Price = max(Asking, Bid Avg) for safety, or just Asking if Bid Avg is low.
                    # For simplicity, let's use Asking Price as the target "Buy Price" if available.
                    buy_price = ask if ask > 0 else bid_avg
                    
                    # 2. Value Difference
                    # If Est > Buy, it's positive (Good deal)
                    diff = est - buy_price
                    
                    # 3. ROI
                    if buy_price > 0:
                        roi = (diff / buy_price) * 100
                    else:
                        roi = 0.0
                        
                    p["buy_price"] = buy_price
                    p["value_diff"] = diff
                    p["roi"] = round(roi, 2)
                    
                    # 4. Forecast Sell: (Estimated / 2) * 0.8
                    p["forecast_sell"] = int((est / 2) * 0.8) - buy_price
                    
                except Exception as e:
                    print(f"Error calculating metrics for {p.get('id')}: {e}")
                    p["buy_price"] = 0
                    p["value_diff"] = 0
                    p["roi"] = 0
                    p["forecast_sell"] = 0
            
            # Sort by Value Diff Descending
            results.sort(key=lambda x: x.get("value_diff", 0), reverse=True)
            
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
                
                # SHEET 1: All Players (Attributes - Upsert)
                # Filter strictly for attribute columns + ID. Exclude financial data.
                drop_cols = ["estimated_value", "asking_price", "buy_price", "value_diff", 
                             "roi", "deadline", "bids_count", "bids_avg", "forecast_sell"]
                
                # Keep only columns that are NOT in drop_cols (but keep if they exist)
                attr_cols = [c for c in df.columns if c not in drop_cols]
                df_attributes = df[attr_cols].copy()
                
                print("Uploading to 'All Players' sheet (Attributes Only)...")
                upload_to_sheets(df_attributes, SPREADSHEET_ID, "All Players")
                
                # SHEET 2: Transfer Info (Market Data - Replace)
                # This sheet should track the CURRENT market status.
                # Columns: ID, Name, Position, Age, Est Value, Asking Price, Buy Price, Value Diff, ROI, Deadline, Forecast Sell
                market_cols = ["id", "name", "position", "age", "Quality", "Potential", 
                               "estimated_value", "asking_price", "buy_price", "value_diff", "roi", "forecast_sell", "deadline", "last_updated", "url"]
                               
                df_market = df[[c for c in market_cols if c in df.columns]].copy()
                
                # For Market Info, we often want to REPLACE the sheet content because sold players should be removed?
                # Or do we want to upsert too? User said "store in another tab sheet".
                # Usually transfer lists change. If we upsert, we keep old dead listings. 
                # Let's REPLACE 'Transfer Info' to show strictly what is currently on the market from this scrape.
                
                print("Uploading to 'Transfer Info' sheet...")
                try:
                     # Re-use upload_to_sheets but we need to clear it first or logic is inside?
                     # upload_to_sheets uses Upsert logic.
                     # We'll make a direct call OR modify upload_to_sheets to support mode.
                     # For now, let's just clear and upload manually here to avoid breaking the function.
                     
                     scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
                     creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
                     client = gspread.authorize(creds)
                     spreadsheet = client.open_by_key(SPREADSHEET_ID)
                     
                     try:
                        sheet_market = spreadsheet.worksheet("Transfer Info")
                     except gspread.WorksheetNotFound:
                        sheet_market = spreadsheet.add_worksheet(title="Transfer Info", rows=1000, cols=20)
                     
                     sheet_market.clear()
                     market_data = [df_market.columns.tolist()] + df_market.fillna("").values.tolist()
                     sheet_market.update(market_data, value_input_option="USER_ENTERED")
                     print("✓ Replaced 'Transfer Info' sheet with current market data.")
                     
                except Exception as e:
                    print(f"Error uploading Transfer Info: {e}")
            
        else:
            print("Credentials missing.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        scraper.stop()

if __name__ == "__main__":
    main()
