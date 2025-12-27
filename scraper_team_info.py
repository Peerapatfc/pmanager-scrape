from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import time

class TeamInfoScraper:
    def __init__(self):
        self.base_url = "https://www.pmanager.org"
        self.browser = None
        self.page = None
        self.playwright = None

    def start(self, headless=True):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.page = self.browser.new_page()

    def stop(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def login(self, username, password):
        print(f"Logging in as {username}...")
        try:
            self.page.goto(f"{self.base_url}/default.asp")
            if self.page.query_selector("#utilizador"):
                self.page.fill("#utilizador", username)
                self.page.fill("#password", password)
                self.page.click(".btn-login")
                self.page.wait_for_load_state("networkidle")
                print("Login submitted.")
            else:
                print("Login form not found. Already logged in?")
        except Exception as e:
            print(f"Login failed: {e}")
            raise

    def get_team_info(self):
        print("Navigating to Team Info page...")
        self.page.goto(f"{self.base_url}/info.asp")
        self.page.wait_for_load_state("networkidle")
        
        # Explicit wait for table content to ensure load
        try:
            self.page.wait_for_selector("table.table_border", timeout=5000)
        except:
            pass
            
        content = self.page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        info = {}
        
        # Helper function to extract value based on label
        def extract_value(label_text, parent_tag='td'):
            # Find the label text
            element = soup.find(string=re.compile(re.escape(label_text)))
            if element:
                # Usually values are in the next td or in a structure nearby
                # The provided DOM shows labels in class="comentarios" and values in class="team_players"
                # They are often in the same tr
                parent_td = element.find_parent('td')
                if parent_td:
                    # Try finding the next td which usually holds the value
                    value_td = parent_td.find_next_sibling('td')
                    if value_td:
                        return value_td.get_text(strip=True, separator=" ")
            return "N/A"

        # General Info
        info['manager'] = extract_value("Manager")
        info['team_name'] = extract_value("Name") # Might pick up Stadium Name if not careful, but first match should be team name in General Info table
        
        # Team Name specific logic (to avoid confusion with Stadium Name)
        # We can narrow search scope if needed, but BeautifulSoup's find usually gets first occurrence.
        # "Name" in "General Info" table comes before "Name" in "Stadium" table.
        
        # Economy
        info['available_funds'] = extract_value("Available Funds")
        info['financial_situation'] = extract_value("Financial Situation")
        info['wage_average'] = extract_value("Wage Average")
        info['wages_sum'] = extract_value("Wages Sum")
        info['wage_roof'] = extract_value("Wage Roof of Club")
        
        # Team Stats
        info['academy'] = extract_value("Academy")
        info['players_count'] = extract_value("Players")
        info['age_average'] = extract_value("Age Average")
        info['players_value'] = extract_value("Players Value")
        info['team_reputation'] = extract_value("Team Reputation")
        info['current_division'] = extract_value("Current Division")
        info['fan_club_size'] = extract_value("Fan Club Size")
        
        # Clean up monetary values (remove " baht" and dots)
        for key in ['available_funds', 'wages_sum', 'wage_roof', 'players_value', 'wage_average']:
            if key in info and info[key] != "N/A":
                # Remove " baht" and everything after + (for wages sum)
                clean_val = info[key].split('+')[0].strip() # Handle "5.264.850 baht (+ 1.314.550 baht)"
                clean_val = re.sub(r'[^\d]', '', clean_val)
                try:
                    info[f"{key}_int"] = int(clean_val)
                except:
                    info[f"{key}_int"] = 0

        return info
