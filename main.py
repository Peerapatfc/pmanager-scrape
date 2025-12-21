import os
from dotenv import load_dotenv
from scraper import PMScraper
import pandas as pd


def main():
    load_dotenv()
    username = os.getenv("PM_USERNAME")
    password = os.getenv("PM_PASSWORD")

    if not username or not password:
        print("Error: PM_USERNAME and PM_PASSWORD must be set in .env file")
        # We'll continue for now since we might just be testing the setup
    
    print("Starting scraper...")
    scraper = PMScraper()
    try:
        scraper.start(headless=False) 
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
                
                # Verify filter
                status = "OK" if ask_price < 1000000 else "FILTER FAIL"
                print(f"[{i+1}/{len(player_ids)}] ID: {pid} | Est. Value: {est_val:,} | Asking: {ask_price:,} [{status}]")
                
                if ask_price < 1000000:
                    results.append(data)
                
            # 3. Sort by Value (Descending)
            results.sort(key=lambda x: x["estimated_value"], reverse=True)
            
            # 4. List Top 5
            print("\n" + "="*60)
            print("TOP 5 PLAYERS BY ESTIMATED TRANSFER VALUE (Asking Price < 1M Verified)")
            print("="*60)
            
            for i, p in enumerate(results[:5]):
                print(f"{i+1}. Player ID: {p['id']}")
                print(f"   Est. Value: {p['estimated_value']:,} baht")
                print(f"   Asking Price: {p['asking_price']:,} baht")
                print(f"   Deadline: {p['deadline']}")
                print(f"   Bids: {p['bids_count']} | Avg: {p['bids_avg']}")
                print(f"   Link: https://www.pmanager.org/ver_jogador.asp?jog_id={p['id']}")
                print("-" * 60)
                
            # Optional: Save to CSV
            df = pd.DataFrame(results)
            df.to_csv("transfer_targets.csv", index=False)
            print("Saved all results to transfer_targets.csv")
            
        else:
            print("Skipping login (no credentials or default credentials)")
            print("Please update .env with actual credentials.")
 

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        scraper.stop()

if __name__ == "__main__":
    main()
