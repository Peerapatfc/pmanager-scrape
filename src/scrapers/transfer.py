import re
import time
from bs4 import BeautifulSoup
from src.scrapers.base import BaseScraper
from src.core.logger import logger
from src.core.utils import clean_currency

class TransferScraper(BaseScraper):
    def search_transfer_list(self, search_url=None, max_pages=150):
        if search_url:
            logger.info(f"Navigating to Custom Search: {search_url}")
            current_url = search_url
        else:
            logger.info("Navigating to ALL players search...")
            # Default URL
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

        while page_num <= max_pages:
            logger.info(f"Scraping page {page_num}...")
            self.page.goto(current_url)
            self.page.wait_for_load_state("networkidle")

            content = self.page.content()
            soup = BeautifulSoup(content, 'html.parser')

            # Extract players
            # Pattern: comprar_jog_lista.asp?jg_id=XXXX
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
            logger.info(f"  Found {count} players on page {page_num}.")
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
                logger.info("No next page found. Stopping.")
                break

        unique_players = list(set(all_players))
        logger.info(f"Total unique players found: {len(unique_players)}")
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
        data["bids_avg"] = "0"

        try:
             # Find financial texts
             def get_val(label, is_curr=True):
                 node = soup_neg.find(string=re.compile(label))
                 if node:
                     parent = node.find_parent('td')
                     if parent:
                         val_td = parent.find_next_sibling('td')
                         if val_td:
                             txt = val_td.get_text(strip=True)
                             if is_curr:
                                 return clean_currency(txt)
                             return txt
                 return None

             data["estimated_value"] = get_val("Estimated Transfer Value") or 0
             data["asking_price"] = get_val("Asking Price for Bid") or 0
             data["deadline"] = soup_neg.find(string="Deadline").find_parent('td').find_next_sibling('td').get_text(strip=True, separator=" ") if soup_neg.find(string="Deadline") else "N/A"
             
             bids_node = soup_neg.find(string="Bids")
             if bids_node:
                 data["bids_count"] = bids_node.find_parent('td').find_next_sibling('td').get_text(strip=True)
                 
             bids_avg_node = soup_neg.find(string="Bids Average (Scout)")
             if bids_avg_node:
                  data["bids_avg"] = bids_avg_node.find_parent('td').find_next_sibling('td').get_text(strip=True)

        except Exception as e:
            logger.error(f"Error scraping financials for {player_id}: {e}")

        # --- PART 2: Skills (Profile Page) ---
        profile_url = data["url"]
        self.page.goto(profile_url)
        try:
           self.page.wait_for_selector("div#infos", timeout=3000)
        except:
           pass
        
        soup = BeautifulSoup(self.page.content(), 'html.parser')

        # Helper to find general info (Position, Age, etc)
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

        # Reports
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

    def get_player_history(self, player_id):
        """Scrape transfer history"""
        history_url = f"{self.base_url}/marcos_jog.asp?jog_id={player_id}"
        logger.debug(f"Checking history for {player_id}...")
        
        try:
            self.page.goto(history_url)
            try:
                self.page.wait_for_selector("div#tabela_titulo", timeout=3000)
            except:
                pass
            
            soup = BeautifulSoup(self.page.content(), 'html.parser')
            
            transfers_header = None
            for div in soup.find_all("div", id="tabela_titulo"):
                if "Transfers" in div.get_text(strip=True):
                    transfers_header = div
                    break
            
            if transfers_header:
                transfers_table = transfers_header.find_next("table", class_="table_border")
                if transfers_table:
                    rows = transfers_table.find_all("tr", class_=["list1", "list2"])
                    if rows:
                        first_row = rows[0]
                        cols = first_row.find_all("td")
                        if len(cols) >= 4:
                            val_text = cols[3].get_text(strip=True)
                            return clean_currency(val_text)
        except Exception as e:
            logger.error(f"Error scraping history for {player_id}: {e}")

        return 0

    def get_bid_info(self, player_id):
        """Quick check for bid info"""
        neg_url = f"{self.base_url}/comprar_jog_lista.asp?jg_id={player_id}"
        data = {
            "estimated_value": 0,
            "bids_count": 0,
            "bids_avg": "0",
            "deadline": "N/A"
        }
        
        try:
            self.page.goto(neg_url)
            self.page.wait_for_selector("body", timeout=3000)
            soup = BeautifulSoup(self.page.content(), 'html.parser')
            
            def get_val(label, is_curr=True):
                 node = soup.find(string=re.compile(label))
                 if node:
                     parent = node.find_parent('td')
                     if parent:
                         val_td = parent.find_next_sibling('td')
                         if val_td:
                             txt = val_td.get_text(strip=True)
                             if is_curr: return clean_currency(txt)
                             return txt
                 return None

            data["estimated_value"] = get_val("Estimated Transfer Value") or 0
            
            dl = soup.find(string="Deadline")
            if dl: 
                parent = dl.find_parent('td')
                if parent:
                    val_td = parent.find_next_sibling('td')
                    if val_td:
                        data["deadline"] = val_td.get_text(strip=True, separator=" ")
            
            bids = soup.find(string="Bids")
            if bids:
                 parent = bids.find_parent('td')
                 if parent:
                    val_td = parent.find_next_sibling('td')
                    if val_td:
                        txt = val_td.get_text(strip=True)
                        if txt.isdigit(): data["bids_count"] = int(txt)

            bavg = soup.find(string="Bids Average (Scout)")
            if bavg:
                 parent = bavg.find_parent('td')
                 if parent:
                    val_td = parent.find_next_sibling('td')
                    if val_td:
                        data["bids_avg"] = val_td.get_text(strip=True)
        
        except Exception as e:
            logger.error(f"Error scraping bid info for {player_id}: {e}")
            
        return data
