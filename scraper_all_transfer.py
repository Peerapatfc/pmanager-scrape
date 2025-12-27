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

    def search_transfer_list(self):
        """Search using the 'All Players' filter provided by user"""
        print("Navigating to ALL players search...")
        
        # URL provided by user
        base_search_url = (
            "https://www.pmanager.org/procurar.asp?action=proc_jog&nome=&pos=0&nacional=-1&lado=-1"
            "&idd_op=%3C&idd=Any&temp_op=%3C&temp=Any&expe_op=%3E%3D&expe=Any&con_op=%3C&con=Any"
            "&pro_op=%3E&pro=Any&vel_op=%3E&vel=Any&forma_op=%3E&forma=Any&cab_op=%3E&cab=Any"
            "&ord_op=%3C%3D&ord=Any&cul_op=%3E&cul=Any&pre_op=%3E&pre=Any&forca_op=%3E&forca=Any"
            "&lesionado=Any&prog_op=%3E&prog=Any&tack_op=%3E&tack=Any&internacional=Any&passe_op=%3E&passe=Any"
            "&pais=-1&rem_op=%3E&rem=Any&tec_op=%3E&tec=Any&jmaos_op=%3E&jmaos=Any&saidas_op=%3E&saidas=Any"
            "&reflexos_op=%3E&reflexos=Any&agilidade_op=%3E&agilidade=Any&B1=Pesquisar&field=&pid=1"
            "&sort=0&pv=1&qual_op=%3E&qual=Any&talento=Any"
        )
        
        current_url = base_search_url
        page_num = 1
        all_players = []
        max_pages = 150  # Limited to 2 pages for testing/performance as requested implicitly by "try to scrape"
        
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
        """Visit player profile and extract detailed skills/attributes"""
        url = f"{self.base_url}/ver_jogador.asp?jog_id={player_id}"
        # print(f"  Scraping details for {player_id}...")
        self.page.goto(url)
        
        try:
           self.page.wait_for_selector("div#infos", timeout=3000)
        except:
           pass
        
        content = self.page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        data = {"id": player_id, "url": url}
        
        # --- 1. General Info ---
        # Helper to find text in team_players class next to label
        def get_general_info(label):
            # Try to find 'b' tag with label
            b_tag = soup.find('b', string=label)
            if b_tag:
                 # Usually the value is in a sibling td with class 'team_players'
                 # Structure: <td align=right><b>Label</b></td> <td>..</td> <td class=team_players>Value</td>
                 parent = b_tag.find_parent('td')
                 if parent:
                      value_td = parent.find_next_sibling('td', class_='team_players')
                      if value_td:
                          return value_td.get_text(strip=True)
                      # Sometimes there's a spacer td in between
                      next_td = parent.find_next_sibling('td')
                      if next_td and not next_td.get_text(strip=True):
                           value_td = next_td.find_next_sibling('td')
                           if value_td:
                               return value_td.get_text(strip=True)
            return "N/A"

        data["name"] = soup.find('font', size="+1").get_text(strip=True) if soup.find('font', size="+1") else "N/A"
        data["position"] = get_general_info("Position")
        data["age"] = get_general_info("Age").replace("Years", "").strip()
        data["nationality"] = get_general_info("Nationality")
        
        # --- 2. Skills (Dynamic) ---
        # We look for tables inside divs 'principais', 'terciarios' (some might be hidden but BeautifulSoup sees them)
        # Structure: <td class="list1" or "list2" align="left"><b>SkillName</b></td> ... <td align="center">Value</td>
        
        skill_count = 0
        
        # Find all tds that might contain skill names (bold text inside list1/list2)
        # We search for td with class list1 or list2
        potential_skill_rows = soup.find_all('td', class_=['list1', 'list2'])
        
        for td in potential_skill_rows:
            b_tag = td.find('b')
            if b_tag:
                skill_name = b_tag.get_text(strip=True)
                
                # Filter out non-skill labels if necessary (e.g., "Health", "Fitness" are also in this format)
                # But we actually want them too! user asked for "player data".
                
                # The value is usually in the next 'td' with align='center' that contains a number
                # Or simply the next sibling td might be a bar, then next is value.
                
                # Check next siblings
                siblings = td.find_next_siblings('td')
                skill_value = None
                
                for sib in siblings:
                    text = sib.get_text(strip=True)
                    if text.isdigit():
                        skill_value = int(text)
                        break
                    # Sometimes value is explicitly formatted? 
                    # If not digit found, it might be string (e.g. Health 100%, Fitness Completely Fit)
                    if not skill_value and text and "Fit" in text:
                         skill_value = text
                         break
                    if not skill_value and "%" in text:
                         skill_value = text 
                         break
                
                if skill_value is not None:
                     data[skill_name] = skill_value
                     skill_count += 1
                elif "Fitness" in skill_name:
                     # Fitness often has value in sibling but text based
                     if siblings:
                         data[skill_name] = siblings[0].get_text(strip=True)

        # --- 3. Player Report (Quality/Potential) ---
        # These are also in list1/list2 usually
        # "Quality", "Potential", "Penalties"
        # Often represented by bars, so value might be text description in next td
        # e.g. Quality -> ... -> Formidable (text)
        
        report_labels = ["Quality", "Potential", "Affected Quality"]
        for label in report_labels:
             # Logic might be already covered by dynamic loop above if they follow same structure
             # But usually Report values are text (e.g. "Formidable"), not numbers 0-20
             if label not in data:
                  b_tag = soup.find('b', string=label)
                  if b_tag:
                       parent = b_tag.find_parent('td')
                       if parent:
                            # Look for text value in siblings
                            siblings = parent.find_next_siblings('td')
                            for sib in siblings:
                                 txt = sib.get_text(strip=True)
                                 # Skip if it's just the bar image td
                                 if txt: 
                                      data[label] = txt
                                      break

        return data
