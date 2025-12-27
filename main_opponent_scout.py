import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from scraper_opponent import OpponentScraper
from main_all_transfer import upload_to_sheets  # Reuse upsert logic

# Google Sheets Config
SPREADSHEET_ID = "1F8FWV9w1gNAGbGDd6RG929dx2jAcM-N6p2ve9fOwSfU"
SHEET_NAME = "All Players"

def main():
    load_dotenv()
    username = os.getenv("PM_USERNAME")
    password = os.getenv("PM_PASSWORD")

    if not username or not password:
        print("Error: PM_USERNAME and PM_PASSWORD must be set in .env file")
        return
        
    # Get Team URL from args
    if len(sys.argv) < 2:
        print("Usage: python main_opponent_scout.py <TEAM_URL_OR_ID>")
        print("Example: python main_opponent_scout.py https://www.pmanager.org/ver_equipa.asp?equipa=35126")
        return
        
    input_arg = sys.argv[1]
    
    # Construct URL if only ID is given
    if "pmanager.org" not in input_arg:
        if input_arg.isdigit():
            team_url = f"https://www.pmanager.org/ver_equipa.asp?equipa={input_arg}&vjog=1"
        else:
            print("Invalid input. Please provide a full URL or a numeric Team ID.")
            return
    else:
        team_url = input_arg

    print(f"Starting Opponent Scout for: {team_url}")
    scraper = OpponentScraper()
    
    try:
        # CI/Headless Check
        is_ci = os.getenv("CI", "false").lower() == "true"
        scraper.start(headless=is_ci)
        
        if username and password:
            scraper.login(username, password)
            
            # 1. Get Player IDs from Team Page
            player_ids = scraper.get_team_players(team_url)
            
            if not player_ids:
                print("No players found on this team page.")
                return

            # 2. Get Details for each (Reusing deep scout logic)
            results = []
            print(f"Scouting {len(player_ids)} players...")
            
            for i, pid in enumerate(player_ids):
                print(f"[{i+1}/{len(player_ids)}] Scouting ID: {pid}...", end="\r")
                try:
                    data = scraper.get_player_details(pid)
                    # Add tag to source to know it came from opponent scout? Optional.
                    # data["scout_source"] = "Opponent: " + team_url
                    results.append(data)
                except Exception as e:
                    print(f"\nError scraping {pid}: {e}")
            
            print(f"\nSuccessfully scouted {len(results)} players.")
            
            if results:
                # 3. Prepare DataFrame
                df = pd.DataFrame(results)
                
                # Timestamp
                thailand_time = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
                df["last_updated"] = thailand_time
                
                # Reorder columns
                cols = list(df.columns)
                priority_cols = ["id", "name", "position", "age", "team", "nationality", "Quality", "Potential", "url"]
                new_order = [c for c in priority_cols if c in cols] + [c for c in cols if c not in priority_cols]
                df = df[new_order]

                # 4. Upsert to Google Sheets
                upload_to_sheets(df, SPREADSHEET_ID, SHEET_NAME)
            
        else:
            print("Credentials missing.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        scraper.stop()

if __name__ == "__main__":
    main()
