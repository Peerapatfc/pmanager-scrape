import os
from datetime import datetime
import pandas as pd
from src.config import config
from src.core.logger import logger
from src.scrapers.bot_team import BotTeamScraper
from src.services.supabase_client import SupabaseManager

def main():
    config.validate()
    
    scraper = BotTeamScraper(base_url="https://www.pmanager.org")
    scraper.start(headless=config.HEADLESS_MODE)
    
    bot_opportunities = []
    
    try:
        scraper.login(config.PM_USERNAME, config.PM_PASSWORD)
        
        logger.info("Starting BOT Team Scrape...")
        
        # 1. Scrape league tree to find bot teams
        # Scrape top league and second division only
        bot_teams = scraper.scrape_league_tree(max_division=2)
        
        if not bot_teams:
            logger.warning("No bot teams found!")
            return
            
        logger.info(f"Found {len(bot_teams)} total BOT teams. Extracting rosters...")
        
        # 2. Extract rosters
        all_bot_players = []
        for team in bot_teams:
            logger.debug(f"Getting roster for {team['name']} ({team['country']} D{team['division']})")
            pids = scraper.get_team_roster(team['id'])
            for pid in pids:
                all_bot_players.append((pid, team['name']))
                
        logger.info(f"Loaded {len(all_bot_players)} players from BOT teams. Evaluating...")
        
        # 3. Evaluate each player against filter criteria
        # Loop limit or progress indicator
        for i, (pid, team_name) in enumerate(all_bot_players):
            if i > 0 and i % 50 == 0:
                logger.info(f"Evaluating player {i}/{len(all_bot_players)}...")
            try:
                result = scraper.evaluate_player(pid, team_name)
                if result:
                    bot_opportunities.append(result)
            except Exception as e:
                logger.error(f"Error evaluating player {pid}: {e}")
                
    except Exception as e:
        logger.error(f"Global Scraper Error: {e}")
    finally:
        scraper.stop()

    if not bot_opportunities:
        logger.warning("No bot opportunities matched the criteria.")
        return

    # Process and Upload
    df = pd.DataFrame(bot_opportunities)
    df['scraped_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    csv_file = "bot_opportunities.csv"
    df.to_csv(csv_file, index=False)
    logger.info(f"Saved CSV backup to {csv_file}")
    
    # Upload to Supabase
    db = SupabaseManager()
    records = df.to_dict(orient="records")
    db.upsert_bot_opportunities(records)

if __name__ == "__main__":
    main()
