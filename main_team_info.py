import os
import json
from datetime import datetime, timedelta
from src.config import config
from src.core.logger import logger
from src.scrapers.team import TeamInfoScraper
from src.services.supabase_client import SupabaseManager

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
        
        # Upload to Supabase
        db = SupabaseManager()
        db.upsert_team_info(info)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        scraper.stop()

if __name__ == "__main__":
    main()
