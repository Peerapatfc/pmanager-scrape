import re
import math
from datetime import datetime
from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper
from src.core.logger import logger
from src.core.utils import clean_currency

class BotTeamScraper(BaseScraper):
    def __init__(self, base_url="https://www.pmanager.org"):
        super().__init__(base_url=base_url)
        self.accepted_qualities = ["Excellent", "Formidable", "World Class"]

    def get_all_countries(self):
        """Dynamically extract all active countries from the sidebar dropdown."""
        # The dropdown is usually available on most pages, let's load ver_mundo just to be sure
        self.page.goto(f"{self.base_url}/ver_mundo.asp")
        
        try:
            self.page.wait_for_selector("#countryList", timeout=5000)
        except:
            logger.warning("Could not find #countryList dropdown on ver_mundo.asp")
            
        soup = BeautifulSoup(self.page.content(), 'html.parser')
        country_select = soup.find('select', id='countryList')
        
        countries = []
        if country_select:
            for option in country_select.find_all('option'):
                val = option.get('value')
                name = option.get_text(strip=True)
                if val and name:
                    countries.append({"id": val, "name": name})
                    
        return countries

    def scrape_league_tree(self, max_division=None):
        """Scrape all countries and their divisions/series for bot teams."""
        countries = self.get_all_countries()
        if not countries:
            logger.warning("No countries found from dropdown.")
            return []

        all_bot_teams = []
        
        for country in countries:
            cid = country["id"]
            cname = country["name"]
            logger.info(f"--- Scraping Country: {cname} (ID: {cid}) ---")
            
            # Fetch the country's sg= shortcode directly from its National page
            self.page.goto(f"{self.base_url}/ver_pais.asp?nm=1&id={cid}")
            soup_pais = BeautifulSoup(self.page.content(), 'html.parser')
            sg_val = None
            league_link = soup_pais.find('a', href=re.compile(r'classificacao\.asp\?.*sg=', re.IGNORECASE))
            if league_link:
                sg_match = re.search(r'sg=([A-Z0-9]+)', league_link['href'], re.IGNORECASE)
                if sg_match:
                    sg_val = sg_match.group(1)
                    
            if not sg_val:
                logger.warning(f"Could not automatically resolve sg= parameter for {cname}. Skipping.")
                continue
            
            logger.info(f"Resolved {cname} -> sg={sg_val}")
            current_league_url = f"{self.base_url}/classificacao.asp?dv=1&sr=1&vf=1&sg={sg_val}"
            
            while current_league_url:
                teams, next_url = self.get_bot_teams_and_next_league(cname, current_league_url)
                if teams:
                    all_bot_teams.extend(teams)
                
                if next_url:
                    # If heavily constrained by max_division, check it
                    if max_division is not None:
                        dv_match = re.search(r'dv=(\d+)', next_url)
                        if dv_match and int(dv_match.group(1)) > max_division:
                            break
                    
                    current_league_url = f"{self.base_url}/{next_url}" if not next_url.startswith("http") else next_url
                else:
                    break

        # Remove duplicates
        unique_bots = {t['id']: t for t in all_bot_teams}.values()
        return list(unique_bots)

    def get_bot_teams_and_next_league(self, country_name, url):
        """Extract BOT teams from a league table and find the URL to the next series/division."""
        self.page.goto(url)
        
        try:
            self.page.wait_for_selector("table", timeout=3000)
        except:
            pass # Continue and check DOM
            
        soup = BeautifulSoup(self.page.content(), 'html.parser')
        
        dv_match = re.search(r'dv=(\d+)', url)
        sr_match = re.search(r'sr=(\d+)', url)
        dv = dv_match.group(1) if dv_match else "Unknown"
        sr = sr_match.group(1) if sr_match else "1"
        
        bot_teams = []
        
        # Find the league standings table
        league_table = None
        for table in soup.find_all('table'):
            if table.find(lambda t: t.name in ['td', 'th'] and 'Position' in t.text):
                league_table = table
                break
                
        if not league_table:
            league_table = soup
            
        # The team links are either clube.asp?clube=123 or ver_equipa.asp?equipa=123
        links = league_table.find_all('a', href=re.compile(r'(clube\.asp\?clube=|ver_equipa\.asp\?equipa=)\d+', re.IGNORECASE))
        
        # Determine human vs bot
        seen_teams = set()
        for a in links:
            team_id_match = re.search(r'(?:clube=|equipa=)(\d+)', a['href'], re.IGNORECASE)
            if not team_id_match:
                continue
            team_id = team_id_match.group(1)
            if team_id in seen_teams:
                continue
                
            seen_teams.add(team_id)
            team_name = a.get_text(strip=True)
            # Bold check: Human teams use <a><b>Name</b></a> (bold as child)
            # or <b><a>Name</a></b> (bold as parent)
            child_b = a.find(['b', 'strong'])
            parent_b = a.find_parent(['b', 'strong'])
            is_bold = child_b is not None or parent_b is not None
            
            if not is_bold:
                bot_teams.append({
                    "id": team_id,
                    "name": team_name,
                    "country": country_name,
                    "division": dv
                })
                
        # Find next league URL via the new 'fs_arrow_right.gif' (Next Series) or 'fs_arrow_down.gif' (Next Division)
        next_league_url = None
        for img in soup.find_all('img'):
            src = img.get('src', '').lower()
            if 'fs_arrow_right.gif' in src:
                parent_a = img.find_parent('a')
                if parent_a and parent_a.get('href'):
                    next_league_url = parent_a['href']
                    break
        
        if not next_league_url:
            for img in soup.find_all('img'):
                src = img.get('src', '').lower()
                if 'fs_arrow_down.gif' in src:
                    parent_a = img.find_parent('a')
                    if parent_a and parent_a.get('href'):
                        next_league_url = parent_a['href']
                        break
                
        logger.info(f"[{country_name} D{dv}S{sr}] Found {len(bot_teams)} bot teams. Next URL: {next_league_url}")
        return bot_teams, next_league_url

    def get_team_roster(self, team_id):
        """Extract player IDs from a team's roster."""
        url = f"{self.base_url}/ver_equipa.asp?equipa={team_id}&vjog=1"
        self.page.goto(url)
        
        try:
            self.page.wait_for_selector("table", timeout=3000)
        except:
            pass
            
        soup = BeautifulSoup(self.page.content(), 'html.parser')
        
        player_ids = []
        links = soup.find_all('a', href=re.compile(r'ver_jogador\.asp\?jog_id=\d+'))
        for a in links:
            pid = re.search(r'jog_id=(\d+)', a['href']).group(1)
            player_ids.append(pid)
            
        return list(set(player_ids))

    def evaluate_player(self, player_id, team_name):
        """
        Check if the bot player is a good opportunity.
        Requirement: Save all players for the user. (Filters removed)
        """
        # --- 1. Negotiation Page (Financials) ---
        neg_url = f"{self.base_url}/comprar_jog_lista.asp?jg_id={player_id}"
        self.page.goto(neg_url)
        
        try:
            self.page.wait_for_selector("body", timeout=3000)
        except:
            pass
            
        soup_neg = BeautifulSoup(self.page.content(), 'html.parser')
        
        estimated_value = 0
        asking_price = 0
        
        try:
            def get_val(label):
                node = soup_neg.find(string=re.compile(label))
                if node:
                    parent = node.find_parent('td')
                    if parent:
                        val_td = parent.find_next_sibling('td')
                        if val_td:
                            return clean_currency(val_td.get_text(strip=True))
                return 0

            estimated_value = get_val("Estimated Transfer Value") or 0
            asking_price = get_val("Asking Price") or 0
        except Exception as e:
            logger.error(f"Error extracting financials for {player_id}: {e}")
            return None
            
        # Initial Filter: Must be profitable (REMOVED BY USER REQUEST)
        # if asking_price == 0 or asking_price >= estimated_value:
        #     return None
            
        # --- 2. Profile Page (Attributes) ---
        prof_url = f"{self.base_url}/ver_jogador.asp?jog_id={player_id}"
        self.page.goto(prof_url)
        
        try:
            self.page.wait_for_selector("body", timeout=3000)
        except:
            pass
            
        soup_prof = BeautifulSoup(self.page.content(), 'html.parser')
        
        quality = "N/A"
        name = "Unknown"
        age = 0
        position = "N/A"
        
        try:
            name_font = soup_prof.find('font', size="+1")
            if name_font:
                name = name_font.get_text(strip=True)
                
            def get_prof_info(label):
                b_tag = soup_prof.find('b', string=label)
                if b_tag:
                    parent = b_tag.find_parent('td')
                    if parent:
                        # The layout could be immediately next sibling, or one cell over
                        sibs = parent.find_next_siblings('td')
                        for sib in sibs:
                            txt = sib.get_text(strip=True)
                            if txt: return txt
                return "N/A"
                
            quality = get_prof_info("Quality")
            position = get_prof_info("Position")
            age_raw = get_prof_info("Age")
            if age_raw and "Years" in age_raw:
                age = int(age_raw.replace("Years", "").strip())
                
        except Exception as e:
            logger.error(f"Error extracting profile for {player_id}: {e}")
            return None
            
        # Final Filter: Quality must match accepted list (REMOVED BY USER REQUEST to save all players)
        # if quality not in self.accepted_qualities:
        #     return None
            
        value_diff = estimated_value - asking_price
        profit_margin = 0.0
        if asking_price > 0:
            profit_margin = round((value_diff / asking_price) * 100, 2)
        
        logger.info(f"Target Found! {name} ({quality}) - Price: {asking_price}, Est: {estimated_value}")
        
        return {
            "id": player_id,
            "name": name,
            "position": position,
            "age": age,
            "quality": quality,
            "team_name": team_name,
            "estimated_value": estimated_value,
            "asking_price": asking_price,
            "value_diff": value_diff,
            "profit_margin": profit_margin,
            "url": prof_url
        }
