from src.scrapers.base import BaseScraper
from bs4 import BeautifulSoup
import re
from src.core.logger import logger
from src.core.utils import clean_currency

class TeamInfoScraper(BaseScraper):
    def get_team_info(self):
        logger.info("Navigating to Team Info page...")
        self.page.goto(f"{self.base_url}/info.asp")
        self.page.wait_for_load_state("networkidle")
        
        try:
            self.page.wait_for_selector("table.table_border", timeout=5000)
        except:
            pass
            
        content = self.page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        info = {}
        
        def extract_value(label_text):
            element = soup.find(string=re.compile(re.escape(label_text)))
            if element:
                parent_td = element.find_parent('td')
                if parent_td:
                    value_td = parent_td.find_next_sibling('td')
                    if value_td:
                        return value_td.get_text(strip=True, separator=" ")
            return "N/A"

        info['manager'] = extract_value("Manager")
        info['team_name'] = extract_value("Name")
        
        info['available_funds'] = extract_value("Available Funds")
        info['financial_situation'] = extract_value("Financial Situation")
        info['wage_average'] = extract_value("Wage Average")
        info['wages_sum'] = extract_value("Wages Sum")
        info['wage_roof'] = extract_value("Wage Roof of Club")
        
        info['academy'] = extract_value("Academy")
        info['players_count'] = extract_value("Players")
        info['age_average'] = extract_value("Age Average")
        info['players_value'] = extract_value("Players Value")
        info['team_reputation'] = extract_value("Team Reputation")
        info['current_division'] = extract_value("Current Division")
        info['fan_club_size'] = extract_value("Fan Club Size")
        
        for key in ['available_funds', 'wages_sum', 'wage_roof', 'players_value', 'wage_average']:
            if key in info and info[key] != "N/A":
                # Handle "5.264.850 baht (+ 1.314.550 baht)"
                raw_val = info[key].split('+')[0].strip()
                info[f"{key}_int"] = clean_currency(raw_val)
        
        return info
