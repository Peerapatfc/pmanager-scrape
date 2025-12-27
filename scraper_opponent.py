from scraper_all_transfer import AllTransferScraper
from bs4 import BeautifulSoup
import re

class OpponentScraper(AllTransferScraper):
    def get_team_players(self, team_url):
        """Navigate to team page and extract all player IDs"""
        print(f"Navigating to team page: {team_url}")
        self.page.goto(team_url)
        self.page.wait_for_load_state("networkidle")
        
        content = self.page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        player_ids = []
        
        # DOM structure from user:
        # Rows have class "list1" or "list2"
        # Inside, links like "ver_jogador.asp?jog_id=XXXXXXX"
        
        rows = soup.find_all('tr', class_=['list1', 'list2'])
        print(f"Found {len(rows)} rows in squad table.")
        
        for row in rows:
            # Find link with 'jog_id'
            link = row.find('a', href=re.compile(r'ver_jogador\.asp\?jog_id='))
            if link:
                href = link['href']
                try:
                    # Extract ID
                    pid = href.split('jog_id=')[1]
                    player_ids.append(pid)
                except IndexError:
                    continue
                    
        unique_ids = list(set(player_ids))
        print(f"Found {len(unique_ids)} unique players in team.")
        return unique_ids
