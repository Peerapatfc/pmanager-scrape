import sys
from src.config import config
from src.core.logger import logger
from src.scrapers.opponent import OpponentScraper
from src.services.gsheets import SheetManager

def main():
    config.validate()
        
    # Get Team URL from args
    if len(sys.argv) < 2:
        print("Usage: python main_opponent_scout.py <TEAM_URL_OR_ID>")
        return
        
    input_arg = sys.argv[1]
    
    if "pmanager.org" not in input_arg:
        if input_arg.isdigit():
            team_url = f"https://www.pmanager.org/ver_equipa.asp?equipa={input_arg}&vjog=1"
        else:
            logger.error("Invalid input.")
            return
    else:
        team_url = input_arg

    logger.info(f"Starting Opponent Scout (Check Mode) for: {team_url}")
    
    # 1. Fetch Existing Data
    logger.info("Fetching existing player database...")
    sheet_manager = SheetManager()
    existing_records = sheet_manager.get_all_records(config.SHEET_NAME_ALL_PLAYERS)
    
    existing_ids = set()
    for r in existing_records:
        if 'id' in r:
            existing_ids.add(str(r['id']))
            
    logger.info(f"Loaded {len(existing_ids)} players from database.")

    scraper = OpponentScraper(base_url="https://www.pmanager.org")
    
    try:
        scraper.start(headless=config.HEADLESS_MODE)
        scraper.login(config.PM_USERNAME, config.PM_PASSWORD)
            
        # 2. Get Player IDs from Team Page
        opponent_ids = scraper.get_team_players(team_url)
        
        if not opponent_ids:
            logger.warning("No players found on this team page.")
            return

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
            
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        scraper.stop()

if __name__ == "__main__":
    main()
