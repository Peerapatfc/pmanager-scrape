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
    
    db = SupabaseManager()
    
    # 1. Fetch batch of players from DB
    batch_size = 500  # Evaluates 4,000 players/day (120,000 / month) via 8 runs
    players_batch = db.get_batch_for_evaluation(batch_size=batch_size)
    
    if not players_batch:
        logger.warning("No players found in database to evaluate.")
        scraper.stop()
        return

    logger.info(f"Loaded {len(players_batch)} players from database. Evaluating via continuous cycle...")
    
    bot_opportunities = []
    
    try:
        scraper.login(config.PM_USERNAME, config.PM_PASSWORD)
        
        # 2. Evaluate each player
        for i, player in enumerate(players_batch):
            pid = player['id']
            team_name = player.get('team_name', 'Unknown')
            
            if i > 0 and i % 50 == 0:
                logger.info(f"Evaluating player {i}/{len(players_batch)}...")
            
            try:
                result = scraper.evaluate_player(pid, team_name)
                # Regardless of success or failure (None), we MUST update `last_evaluated_at` 
                # to guarantee the continuous cycle doesn't get stuck on bad players.
                if result:
                    result['last_evaluated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    bot_opportunities.append(result)
                else:
                    # Player was invalid - update timestamp to bypass them
                    bot_opportunities.append({
                        "id": pid,
                        "team_name": team_name,
                        "last_evaluated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
            except Exception as e:
                logger.error(f"Error evaluating player {pid}: {e}")
                
    except Exception as e:
        logger.error(f"Global Evaluation Error: {e}")
    finally:
        scraper.stop()

    if not bot_opportunities:
        logger.warning("No bot opportunities evaluated successfully.")
        return

    # Process and Upload
    df = pd.DataFrame(bot_opportunities)
    
    csv_file = "bot_evaluations_batch.csv"
    df.to_csv(csv_file, index=False)
    logger.info(f"Saved CSV backup to {csv_file}")
    
    # Upload to Supabase
    records = df.to_dict(orient="records")
    db.upsert_bot_opportunities(records)

if __name__ == "__main__":
    main()
