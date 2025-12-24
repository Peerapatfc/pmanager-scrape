from playwright.sync_api import sync_playwright
import pandas as pd
import time
from bs4 import BeautifulSoup
import re

class PMScraper:
    def __init__(self):
        self.base_url = "https://www.pmanager.org"
        self.browser = None
        self.page = None
        self.playwright = None

    def start(self, headless=False):
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
                
                # Check if login was successful (e.g. check for logout link or specific element)
                # For now assume success if no error
                print("Login submitted.")
            else:
                print("Login form not found. Already logged in?")
        except Exception as e:
            print(f"Login failed: {e}")
            raise

    def get_search_html(self):
        print("Navigating to search page...")
        # Try a full search query to ensure results are loaded
        # Based on user history: action=proc_jog&nome=&pos=0&nacional=-1
        search_url = f"{self.base_url}/procurar.asp?action=proc_jog&nome=&pos=0&nacional=-1"
        self.page.goto(search_url)
        
        try:
            # Wait for the panel body to have some content or a table
            # We don't know the exact table selector, so we wait a bit or check for a common table class
            self.page.wait_for_load_state("networkidle")
            time.sleep(3) # Extra wait for any dynamic rendering
            
            # Print current URL to debug
            print(f"Current URL: {self.page.url}")
            print(f"Page Title: {self.page.title()}")
            print(f"Body Text Snippet: {self.page.inner_text('body')[:500]}")
            
        except Exception as e:
            print(f"Wait failed: {e}")
            
        return self.page.content()

    def search_transfer_list(self):
        print("Navigating to transfer list search via direct URL...")
        # Direct URL with filters
        # Note: Removing &pid=1 from the base URL so we can append it dynamically for consistency, 
        # or just start with the provided URL and look for next page.
        # The provided URL ends with &talento=Any. Pagination links usually append &pid=X.
        
        # Scenario: Age < 31 and Quality > Very Good (7), Price = Any
        base_search_url = (
            "https://www.pmanager.org/procurar.asp?action=proc_jog&nome=&pos=0&nacional=-1&lado=-1"
            "&idd_op=%3C&idd=31&temp_op=%3C&temp=Any&expe_op=%3E%3D&expe=Any&con_op=%3C&con=Any"
            "&pro_op=%3E&pro=Any&vel_op=%3E&vel=Any&forma_op=%3E&forma=Any&cab_op=%3E&cab=Any"
            "&ord_op=%3C%3D&ord=Any&cul_op=%3E&cul=Any&pre_op=%3E&pre=Any&forca_op=%3E&forca=Any"
            "&lesionado=Any&prog_op=%3E&prog=Any&tack_op=%3E&tack=Any&internacional=Any&passe_op=%3E&passe=Any"
            "&pais=-1&rem_op=%3E&rem=Any&tec_op=%3E&tec=Any&jmaos_op=%3E&jmaos=Any&saidas_op=%3E&saidas=Any"
            "&reflexos_op=%3E&reflexos=Any&agilidade_op=%3E&agilidade=Any&B1=Pesquisar&field=&pid=1"
            "&sort=0&pv=1&qual_op=%3E&qual=7&talento=Any"
        )
        
        current_url = base_search_url
        page_num = 1
        all_players = []
        max_pages = 100 # Safety limit
        
        while page_num <= max_pages:
            print(f"Scraping page {page_num}...")
            self.page.goto(current_url)
            self.page.wait_for_load_state("networkidle")
            
            content = self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract players from current page
            links = soup.find_all('a', href=re.compile(r'comprar_jog_lista\.asp\?jg_id='))
            page_players = []
            for link in links:
                href = link['href']
                try:
                    player_id = href.split('jg_id=')[1]
                    page_players.append(player_id)
                except IndexError:
                    continue
            
            count = len(set(page_players))
            print(f"  Found {count} players on page {page_num}.")
            all_players.extend(page_players)
            
            # Check for next page
            # Link pattern: something with &pid={page_num + 1}
            # We look for an <a> tag where href contains f"&pid={page_num+1}"
            next_page_pid = page_num + 1
            next_link = soup.find('a', href=re.compile(f"&pid={next_page_pid}"))
            
            if next_link:
                # The href in the link might be relative or absolute.
                # Usually relative like "procurar.asp?action=proc_jog...&pid=2..."
                href = next_link['href']
                if not href.startswith("http"):
                    current_url = f"{self.base_url}/{href}"
                else:
                    current_url = href
                page_num += 1
            else:
                print("No next page found. Stopping.")
                break
        
        unique_players = list(set(all_players))
        print(f"Total unique players found across all pages: {len(unique_players)}")
        return unique_players

    def get_estimated_value(self, player_id):
        # Visit negotiation page
        url = f"{self.base_url}/comprar_jog_lista.asp?jg_id={player_id}"
        self.page.goto(url)
        # self.page.wait_for_load_state("networkidle") 
        # Explicit wait for body or title to ensure load
        try:
           self.page.wait_for_selector("body")
        except:
           pass
        
        content = self.page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        data = {"id": player_id, "estimated_value": 0, "asking_price": 0, "deadline": "N/A", "bids_avg": "N/A", "bids_count": "0"}
        
        try:
            # Extract Estimated Transfer Value
            label_est = soup.find(string=re.compile("Estimated Transfer Value"))
            if label_est:
                val_td = label_est.find_parent('td').find_next_sibling('td')
                if val_td:
                    txt = val_td.get_text(strip=True)
                    clean = re.sub(r'[^\d]', '', txt)
                    if clean:
                        data["estimated_value"] = int(clean)

            # Extract Asking Price for Bid
            label_ask = soup.find(string=re.compile("Asking Price for Bid"))
            if label_ask:
                val_td = label_ask.find_parent('td').find_next_sibling('td')
                if val_td:
                    txt = val_td.get_text(strip=True)
                    clean = re.sub(r'[^\d]', '', txt)
                    if clean:
                        data["asking_price"] = int(clean)
            
            # Extract Deadline
            # Selector verified: label "Deadline" in td, value in next sibling td
            label_dead = soup.find(string="Deadline")
            if label_dead:
                val_td = label_dead.find_parent('td').find_next_sibling('td')
                if val_td:
                    # Get text with separator to handle <br> (date vs remaining time)
                    data["deadline"] = val_td.get_text(strip=True, separator=" ")

            # Extract Bids Average (Scout)
            label_avg = soup.find(string="Bids Average (Scout)")
            if label_avg:
                val_td = label_avg.find_parent('td').find_next_sibling('td')
                if val_td:
                    data["bids_avg"] = val_td.get_text(strip=True)

            # Extract Bids Count
            label_bids = soup.find(string="Bids")
            if label_bids:
                val_td = label_bids.find_parent('td').find_next_sibling('td')
                if val_td:
                    data["bids_count"] = val_td.get_text(strip=True)
                        
        except Exception as e:
            print(f"Error extracting value for {player_id}: {e}")
            
        return data
