import os
import json
from datetime import datetime, timedelta
from src.config import config
from src.core.logger import logger
from src.scrapers.team import TeamInfoScraper
from src.services.gsheets import SheetManager

def append_to_sheet(info_dict):
    """Append team info row to Google Sheets"""
    try:
        sheet_manager = SheetManager()
        worksheet = sheet_manager.get_worksheet(sheet_name="Team Info") # Assuming this sheet name logic
        
        # NOTE: Using 'Team Info' from config if added, but let's assume "Team Info" string for now or add to config
        # config.SHEET_NAME_TEAM_INFO doesn't exist yet, using literal as per old script
        
        # Prepare row data
        # UTC+7
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
        
        # Logic: Resize to 2 rows (Header + 1 Data Row), Update Row 2
        # This keeps only the latest status.
        # But we need to ensure header exists?
        # SheetManager doesn't expose resize/append_row easily without direct access.
        # We can use sheet_manager.worksheet object directly if we really need specific logic.
        
        # Direct access to gspread worksheet
        ws = worksheet
        
        if ws.row_count < 1 or not ws.row_values(1):
             header = [
                "Date", "Team Name", "Manager", "Available Funds", "Financial Situation",
                "Wages Sum", "Wage Roof", "Academy", "Players", "Age Average", 
                "Players Value", "Team Reputation", "Division", "Fan Club"
            ]
             ws.append_row(header)
        
        ws.resize(rows=2)
        ws.update([row], range_name="A2", value_input_option="USER_ENTERED")
        
        logger.info(f"Updated Team Info in Google Sheets")
        return True
        
    except Exception as e:
        logger.error(f"Failed to upload to Google Sheets: {e}")
        return False

def main():
    config.validate()
    
    logger.info("Starting Team Info Scraper...")
    scraper = TeamInfoScraper()
    
    try:
        scraper.start(headless=config.HEADLESS_MODE) 
        scraper.login(config.PM_USERNAME, config.PM_PASSWORD)
            
        info = scraper.get_team_info()
        
        logger.info("="*50)
        logger.info("TEAM INFORMATION")
        logger.info("="*50)
        for key, value in info.items():
            if not key.endswith("_int"):
                logger.info(f"{key.replace('_', ' ').title()}: {value}")
        logger.info("="*50)
        
        # Save to JSON
        filename = "team_info.json"
        with open(filename, "w", encoding='utf-8') as f:
            json.dump(info, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Saved team info to {filename}")
        
        append_to_sheet(info)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        scraper.stop()

if __name__ == "__main__":
    main()
