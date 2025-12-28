from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import time

class AllTransferScraper:
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
                # Standard login
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

    def search_transfer_list(self, search_url=None):
        """
        Search using a provided URL or the default 'All Players' filter.
        search_url: Optional URL to start scraping from.
        """
        if search_url:
            print(f"Navigating to Custom Search: {search_url}...")
            current_url = search_url
        else:
            print("Navigating to ALL players search...")
            # Default URL provided by user
            current_url = (
                "https://www.pmanager.org/procurar.asp?action=proc_jog&nome=&pos=0&nacional=-1&lado=-1"
                "&idd_op=%3C&idd=Any&temp_op=%3C&temp=Any&expe_op=%3E%3D&expe=Any&con_op=%3C&con=Any"
                "&pro_op=%3E&pro=Any&vel_op=%3E&vel=Any&forma_op=%3E&forma=Any&cab_op=%3E&cab=Any"
                "&ord_op=%3C%3D&ord=Any&cul_op=%3E&cul=Any&pre_op=%3E&pre=Any&forca_op=%3E&forca=Any"
                "&lesionado=Any&prog_op=%3E&prog=Any&tack_op=%3E&tack=Any&internacional=Any&passe_op=%3E&passe=Any"
                "&pais=-1&rem_op=%3E&rem=Any&tec_op=%3E&tec=Any&jmaos_op=%3E&jmaos=Any&saidas_op=%3E&saidas=Any"
                "&reflexos_op=%3E&reflexos=Any&agilidade_op=%3E&agilidade=Any&B1=Pesquisar&field=&pid=1"
                "&sort=0&pv=1&qual_op=%3E&qual=Any&talento=Any"
            )
        
        page_num = 1
        all_players = []
        max_pages = 3  # Limited pages per category to avoid timeout
        
        while page_num <= max_pages:
            print(f"Scraping page {page_num}...")
            self.page.goto(current_url)
            self.page.wait_for_load_state("networkidle")
            
            content = self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract players
            links = soup.find_all('a', href=re.compile(r'comprar_jog_lista\.asp\?jg_id='))
            page_players = []
            for link in links:
                try:
                    href = link['href']
                    player_id = href.split('jg_id=')[1]
                    page_players.append(player_id)
                except IndexError:
                    continue
            
            unique_on_page = list(set(page_players))
            count = len(unique_on_page)
            print(f"  Found {count} players on page {page_num}.")
            all_players.extend(unique_on_page)
            
            # Check for next page
            next_page_pid = page_num + 1
            next_link = soup.find('a', href=re.compile(f"&pid={next_page_pid}"))
            
            if next_link:
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
        print(f"Total unique players found: {len(unique_players)}")
        return unique_players

    def get_player_details(self, player_id):
        """Visit negotiation AND profile pages to extract comprehensive data"""
        data = {"id": player_id, "url": f"{self.base_url}/ver_jogador.asp?jog_id={player_id}"}

        # --- PART 1: Financials (Negotiation Page) ---
        neg_url = f"{self.base_url}/comprar_jog_lista.asp?jg_id={player_id}"
        self.page.goto(neg_url)
        try:
             self.page.wait_for_selector("body", timeout=3000)
        except:
             pass
        
        soup_neg = BeautifulSoup(self.page.content(), 'html.parser')
        
        # Init financial keys
        data["estimated_value"] = 0
        data["asking_price"] = 0
        data["deadline"] = "N/A"
        data["bids_count"] = "0"
        data["bids_avg"] = "N/A"

        try:
            # Est Value
            label_est = soup_neg.find(string=re.compile("Estimated Transfer Value"))
            if label_est:
                parent = label_est.find_parent('td')
                if parent:
                    val_td = parent.find_next_sibling('td')
                    if val_td:
                        clean = re.sub(r'[^\d]', '', val_td.get_text(strip=True))
                        if clean: data["estimated_value"] = int(clean)
            
            # Asking Price
            label_ask = soup_neg.find(string=re.compile("Asking Price for Bid"))
            if label_ask:
                parent = label_ask.find_parent('td')
                if parent:
                    val_td = parent.find_next_sibling('td')
                    if val_td:
                        clean = re.sub(r'[^\d]', '', val_td.get_text(strip=True))
                        if clean: data["asking_price"] = int(clean)

            # Deadline
            label_dead = soup_neg.find(string="Deadline")
            if label_dead:
                parent = label_dead.find_parent('td')
                if parent:
                    val_td = parent.find_next_sibling('td')
                    if val_td: data["deadline"] = val_td.get_text(strip=True, separator=" ")
            
            # Bids
            label_bids = soup_neg.find(string="Bids")
            if label_bids:
                parent = label_bids.find_parent('td')
                if parent:
                    val_td = parent.find_next_sibling('td')
                    if val_td: data["bids_count"] = val_td.get_text(strip=True)
            
            label_avg = soup_neg.find(string="Bids Average (Scout)")
            if label_avg:
                parent = label_avg.find_parent('td')
                if parent:
                    val_td = parent.find_next_sibling('td')
                    if val_td: data["bids_avg"] = val_td.get_text(strip=True)

        except Exception as e:
            print(f"Error scraping financials for {player_id}: {e}")

        # --- PART 2: Skills (Profile Page) ---
        profile_url = data["url"]
        self.page.goto(profile_url)
        try:
           self.page.wait_for_selector("div#infos", timeout=3000)
        except:
           pass
        
        soup = BeautifulSoup(self.page.content(), 'html.parser')

        # Helper to find general info
        def get_general_info(label):
            b_tag = soup.find('b', string=label)
            if b_tag:
                 parent = b_tag.find_parent('td')
                 if parent:
                      value_td = parent.find_next_sibling('td', class_='team_players')
                      if value_td: return value_td.get_text(strip=True)
                      next_td = parent.find_next_sibling('td')
                      if next_td and not next_td.get_text(strip=True):
                           value_td = next_td.find_next_sibling('td')
                           if value_td: return value_td.get_text(strip=True)
            return "N/A"

        data["name"] = soup.find('font', size="+1").get_text(strip=True) if soup.find('font', size="+1") else "N/A"
        data["position"] = get_general_info("Position")
        data["age"] = get_general_info("Age").replace("Years", "").strip()
        data["nationality"] = get_general_info("Nationality")
        
        # Skill Extraction
        potential_skill_rows = soup.find_all('td', class_=['list1', 'list2'])
        for td in potential_skill_rows:
            b_tag = td.find('b')
            if b_tag:
                skill_name = b_tag.get_text(strip=True)
                siblings = td.find_next_siblings('td')
                skill_value = None
                
                for sib in siblings:
                    text = sib.get_text(strip=True)
                    if text.isdigit():
                        skill_value = int(text)
                        break
                    if not skill_value and text and ("Fit" in text or "%" in text):
                         skill_value = text
                         break
                
                if skill_value is not None:
                     data[skill_name] = skill_value
                elif "Fitness" in skill_name and siblings:
                     data[skill_name] = siblings[0].get_text(strip=True)

        # Reports (Quality/Potential)
        for label in ["Quality", "Potential", "Affected Quality"]:
             if label not in data:
                  b_tag = soup.find('b', string=label)
                  if b_tag:
                       parent = b_tag.find_parent('td')
                       if parent:
                            siblings = parent.find_next_siblings('td')
                            for sib in siblings:
                                 txt = sib.get_text(strip=True)
                                 if txt: 
                                      data[label] = txt
                                      break

        return data
