import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from scraper_team_info import TeamInfoScraper
import gspread
from google.oauth2.service_account import Credentials

# Google Sheets Configuration
SPREADSHEET_ID = "1F8FWV9w1gNAGbGDd6RG929dx2jAcM-N6p2ve9fOwSfU"
SHEET_NAME = "Team Info"

def append_to_sheet(info_dict, spreadsheet_id, sheet_name):
    """Append team info row to Google Sheets"""
    try:
        # Authenticate
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
        client = gspread.authorize(creds)
        
        # Open spreadsheet
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        # Get or create worksheet
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
            # Add header if new
            header = [
                "Date", "Team Name", "Manager", "Available Funds", "Financial Situation",
                "Wages Sum", "Wage Roof", "Academy", "Players", "Age Average", 
                "Players Value", "Team Reputation", "Division", "Fan Club"
            ]
            worksheet.append_row(header)
            
        # Prepare row data
        thailand_time = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
        
        row = [
            thailand_time,
            info_dict.get("team_name", "N/A"),
            info_dict.get("manager", "N/A"),
            info_dict.get("available_funds", "N/A"),
            info_dict.get("financial_situation", "N/A"),
            info_dict.get("wages_sum", "N/A"),
            info_dict.get("wage_roof", "N/A"),
            info_dict.get("academy", "N/A"),
            info_dict.get("players_count", "N/A"),
            info_dict.get("age_average", "N/A"),
            info_dict.get("players_value", "N/A"),
            info_dict.get("team_reputation", "N/A"),
            info_dict.get("current_division", "N/A"),
            info_dict.get("fan_club_size", "N/A")
        ]
        
        # Check if header exists
        if worksheet.row_count < 1 or not worksheet.row_values(1):
             header = [
                "Date", "Team Name", "Manager", "Available Funds", "Financial Situation",
                "Wages Sum", "Wage Roof", "Academy", "Players", "Age Average", 
                "Players Value", "Team Reputation", "Division", "Fan Club"
            ]
             worksheet.append_row(header)

        # UPDATE LOGIC: Replace Row 2 (or append if empty)
        # We want to keep a single row of the LATEST data.
        # Clearing from row 2 onwards is safer.
        
        # Batch update: Clear old data -> Update Row 2
        worksheet.resize(rows=2) # Ensure at least 2 rows exist
        # Update Row 2 specifically
        range_start = "A2"
        # gspread uses list of lists for update
        worksheet.update([row], range_name=range_start, value_input_option="USER_ENTERED")
        
        # Optional: Clean up any extra rows if they existed before?
        # resize(2) handles it mostly, but let's be sure.
        # Actually, simpler approach: Clear sheet, Write Header, Write Row.
        # But user might have custom formatting on header, so let's keep header.
        
        print(f"✓ Updated Team Info in Google Sheets: {sheet_name}")
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
    
    print("Starting Team Info Scraper...")
    scraper = TeamInfoScraper()
    
    try:
        # Use headless mode in CI environment (GitHub Actions)
        is_ci = os.getenv("CI", "false").lower() == "true"
        scraper.start(headless=is_ci) 
        
        # Login
        if username != "your_username":
            scraper.login(username, password)
            
            # Get Team Info
            info = scraper.get_team_info()
            
            # Print to console
            print("\n" + "="*50)
            print("TEAM INFORMATION")
            print("="*50)
            for key, value in info.items():
                if not key.endswith("_int"): # Skip integer versions for display
                    print(f"{key.replace('_', ' ').title()}: {value}")
            print("="*50)
            
            # Save to JSON
            filename = "team_info.json"
            with open(filename, "w", encoding='utf-8') as f:
                json.dump(info, f, indent=4, ensure_ascii=False)
            
            print(f"\nSaved team info to {filename}")
            
            # Upload to Google Sheets
            append_to_sheet(info, SPREADSHEET_ID, SHEET_NAME)
            
        else:
            print("Please update .env with actual credentials.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        scraper.stop()

if __name__ == "__main__":
    main()
