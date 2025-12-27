import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from scraper_opponent import OpponentScraper
import gspread
from google.oauth2.service_account import Credentials

# Google Sheets Config
SPREADSHEET_ID = "1F8FWV9w1gNAGbGDd6RG929dx2jAcM-N6p2ve9fOwSfU"
SHEET_NAME = "All Players"

def get_existing_ids(spreadsheet_id, sheet_name):
    """Fetch all Player IDs from the Google Sheet"""
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
        client = gspread.authorize(creds)
        
        sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
        records = sheet.get_all_records()
        
        # Assume 'id' column exists
        ids = set()
        for r in records:
            if 'id' in r:
                ids.add(str(r['id']))
        return ids, records
    except Exception as e:
        print(f"Error fetching existing IDs: {e}")
        return set(), []

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
        return
        
    input_arg = sys.argv[1]
    
    if "pmanager.org" not in input_arg:
        if input_arg.isdigit():
            team_url = f"https://www.pmanager.org/ver_equipa.asp?equipa={input_arg}&vjog=1"
        else:
            print("Invalid input.")
            return
    else:
        team_url = input_arg

    print(f"Starting Opponent Scout (Check Mode) for: {team_url}")
    
    # 1. Fetch Existing Data
    print("Fetching existing player database...")
    existing_ids, existing_records = get_existing_ids(SPREADSHEET_ID, SHEET_NAME)
    print(f"Loaded {len(existing_ids)} players from database.")

    scraper = OpponentScraper()
    
    try:
        is_ci = os.getenv("CI", "false").lower() == "true"
        scraper.start(headless=is_ci)
        
        if username and password:
            scraper.login(username, password)
            
            # 2. Get Player IDs from Team Page
            opponent_ids = scraper.get_team_players(team_url)
            
            if not opponent_ids:
                print("No players found on this team page.")
                return

            print(f"Found {len(opponent_ids)} players on opponent team.")
            
            # 3. Check for matches
            matches = []
            for pid in opponent_ids:
                if str(pid) in existing_ids:
                    matches.append(pid)
            
            # 4. Report Results
            print("\n" + "="*50)
            print("SCOUT REPORT")
            print("="*50)
            
            if matches:
                print(f"🚨 FOUND {len(matches)} MATCHES IN DATABASE! 🚨")
                print("The following opponent players are already on your watchlist:")
                
                # Find details from existing records to display name
                for pid in matches:
                    # Find record
                    rec = next((r for r in existing_records if str(r.get('id')) == str(pid)), None)
                    name = rec.get('name', 'Unknown') if rec else 'Unknown'
                    pos = rec.get('position', '?') if rec else '?'
                    
                    print(f"- [{pos}] {name} (ID: {pid})")
                    print(f"  Link: https://www.pmanager.org/ver_jogador.asp?jog_id={pid}")
                
            else:
                print("✅ Clean Scout: None of the opponent's players are in your database.")
            
            print("="*50)
            
        else:
            print("Credentials missing.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        scraper.stop()

if __name__ == "__main__":
    main()
