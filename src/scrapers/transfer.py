"""
Transfer market scraper for PManager.org.

Provides :class:`TransferScraper` which walks the global transfer market,
collects player IDs, and extracts per-player financial and skill data.
"""

import re
from typing import Any

from bs4 import BeautifulSoup

from src.core.logger import logger
from src.core.utils import clean_currency
from src.scrapers.base import BaseScraper


class TransferScraper(BaseScraper):
    """Scrapes the PManager transfer market listing and individual player pages."""

    #: Default URL that searches for all listed players (no filters applied).
    SEARCH_URL_TEMPLATE: str = (
        "https://www.pmanager.org/procurar.asp?action=proc_jog&nome=&pos=0&nacional=-1&lado=-1"
        "&idd_op=%3C&idd=Any&temp_op=%3C&temp=Any&expe_op=%3E%3D&expe=Any&con_op=%3C&con=Any"
        "&pro_op=%3E&pro=Any&vel_op=%3E&vel=Any&forma_op=%3E&forma=Any&cab_op=%3E&cab=Any"
        "&ord_op=%3C%3D&ord=Any&cul_op=%3E&cul=Any&pre_op=%3E&pre=Any&forca_op=%3E&forca=Any"
        "&lesionado=Any&prog_op=%3E&prog=Any&tack_op=%3E&tack=Any&internacional=Any&passe_op=%3E&passe=Any"
        "&pais=-1&rem_op=%3E&rem=Any&tec_op=%3E&tec=Any&jmaos_op=%3E&jmaos=Any&saidas_op=%3E&saidas=Any"
        "&reflexos_op=%3E&reflexos=Any&agilidade_op=%3E&agilidade=Any&B1=Pesquisar&field=&pid=1"
        "&sort=0&pv=1&qual_op=%3E&qual=Any&talento=Any"
    )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_val(self, soup: BeautifulSoup, label: str, is_curr: bool = True) -> Any:
        """Extract a table-cell value that follows a label cell.

        Searches ``soup`` for a text node matching ``label``, then returns the
        content of the immediately following ``<td>``.

        Args:
            soup: Parsed HTML tree to search.
            label: Regex-compatible label string to locate.
            is_curr: When ``True`` (default) the value is parsed as a currency
                float via :func:`~src.core.utils.clean_currency`.

        Returns:
            Parsed float if ``is_curr`` is ``True``, raw string otherwise, or
            ``None`` if the label or sibling cell is not found.
        """
        node = soup.find(string=re.compile(label))
        if node:
            parent = node.find_parent("td")
            if parent:
                val_td = parent.find_next_sibling("td")
                if val_td:
                    txt = val_td.get_text(strip=True)
                    return clean_currency(txt) if is_curr else txt
        return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search_transfer_list(
        self, search_url: str | None = None, max_pages: int = 150
    ) -> list[str]:
        """Collect all player IDs from the transfer market listing pages.

        Args:
            search_url: Custom search URL. Falls back to the full-market
                :attr:`SEARCH_URL_TEMPLATE` when omitted.
            max_pages: Upper bound on the number of result pages to traverse.

        Returns:
            Deduplicated list of player ID strings found across all pages.
        """
        if search_url:
            logger.info("Navigating to Custom Search: %s", search_url)
            current_url = search_url
        else:
            logger.info("Navigating to ALL players search...")
            current_url = self.SEARCH_URL_TEMPLATE

        page_num = 1
        all_players: list[str] = []

        while page_num <= max_pages:
            logger.info("Scraping page %d...", page_num)
            self.page.goto(current_url)
            self.page.wait_for_load_state("networkidle")

            content = self.page.content()
            soup = BeautifulSoup(content, "html.parser")

            links = soup.find_all("a", href=re.compile(r"comprar_jog_lista\.asp\?jg_id="))
            page_players: list[str] = []
            for link in links:
                try:
                    href = link["href"]
                    # Use [-1] to safely handle any extra query params after jg_id=
                    player_id = href.split("jg_id=")[-1]
                    page_players.append(player_id)
                except (KeyError, IndexError):
                    continue

            unique_on_page = list(set(page_players))
            logger.info("  Found %d players on page %d.", len(unique_on_page), page_num)
            all_players.extend(unique_on_page)

            next_page_pid = page_num + 1
            next_link = soup.find("a", href=re.compile(f"&pid={next_page_pid}"))

            if next_link:
                href = next_link["href"]
                current_url = href if href.startswith("http") else f"{self.base_url}/{href}"
                page_num += 1
            else:
                logger.info("No next page found. Stopping.")
                break

        unique_players = list(set(all_players))
        logger.info("Total unique players found: %d", len(unique_players))
        return unique_players

    def get_player_details(self, player_id: str) -> dict[str, Any]:
        """Scrape comprehensive data for a single player.

        Visits two pages per player:
        1. The negotiation page (``comprar_jog_lista.asp``) for financials.
        2. The profile page (``ver_jogador.asp``) for skills and attributes.

        Args:
            player_id: Numeric player ID string from PManager.

        Returns:
            Dictionary with keys: ``id``, ``url``, ``estimated_value``,
            ``asking_price``, ``deadline``, ``bids_count``, ``bids_avg``,
            ``name``, ``position``, ``age``, ``nationality``, plus any skill
            names scraped from the profile page.
        """
        data: dict[str, Any] = {
            "id": player_id,
            "url": f"{self.base_url}/ver_jogador.asp?jog_id={player_id}",
        }

        # --- PART 1: Financials (Negotiation Page) ---
        neg_url = f"{self.base_url}/comprar_jog_lista.asp?jg_id={player_id}"
        self.page.goto(neg_url)
        try:
            self.page.wait_for_selector("body", timeout=3000)
        except Exception as e:
            logger.debug("Timeout waiting for negotiation page body (%s): %s", player_id, e)

        soup_neg = BeautifulSoup(self.page.content(), "html.parser")

        data["estimated_value"] = 0
        data["asking_price"] = 0
        data["deadline"] = "N/A"
        data["bids_count"] = "0"
        data["bids_avg"] = "0"

        try:
            data["estimated_value"] = self._get_val(soup_neg, "Estimated Transfer Value") or 0
            data["asking_price"] = self._get_val(soup_neg, "Asking Price for Bid") or 0

            deadline_node = soup_neg.find(string="Deadline")
            if deadline_node:
                deadline_parent = deadline_node.find_parent("td")
                if deadline_parent:
                    deadline_td = deadline_parent.find_next_sibling("td")
                    if deadline_td:
                        data["deadline"] = deadline_td.get_text(strip=True, separator=" ")

            bids_node = soup_neg.find(string="Bids")
            if bids_node:
                bids_parent = bids_node.find_parent("td")
                if bids_parent:
                    bids_td = bids_parent.find_next_sibling("td")
                    if bids_td:
                        data["bids_count"] = bids_td.get_text(strip=True)

            bids_avg_node = soup_neg.find(string="Bids Average (Scout)")
            if bids_avg_node:
                bids_avg_parent = bids_avg_node.find_parent("td")
                if bids_avg_parent:
                    bids_avg_td = bids_avg_parent.find_next_sibling("td")
                    if bids_avg_td:
                        data["bids_avg"] = bids_avg_td.get_text(strip=True)

        except Exception as e:
            logger.error("Error scraping financials for %s: %s", player_id, e, exc_info=True)

        # --- PART 2: Skills (Profile Page) ---
        profile_url = data["url"]
        self.page.goto(profile_url)
        try:
            self.page.wait_for_selector("div#infos", timeout=3000)
        except Exception as e:
            logger.debug("Timeout waiting for profile page infos (%s): %s", player_id, e)

        soup = BeautifulSoup(self.page.content(), "html.parser")

        def get_general_info(label: str) -> str:
            b_tag = soup.find("b", string=label)
            if b_tag:
                parent = b_tag.find_parent("td")
                if parent:
                    value_td = parent.find_next_sibling("td", class_="team_players")
                    if value_td:
                        return value_td.get_text(strip=True)
                    next_td = parent.find_next_sibling("td")
                    if next_td and not next_td.get_text(strip=True):
                        value_td = next_td.find_next_sibling("td")
                        if value_td:
                            return value_td.get_text(strip=True)
            return "N/A"

        name_font = soup.find("font", size="+1")
        data["name"] = name_font.get_text(strip=True) if name_font else "N/A"
        data["position"] = get_general_info("Position")
        data["age"] = get_general_info("Age").replace("Years", "").strip()
        data["nationality"] = get_general_info("Nationality")

        potential_skill_rows = soup.find_all("td", class_=["list1", "list2"])
        for td in potential_skill_rows:
            b_tag = td.find("b")
            if b_tag:
                skill_name = b_tag.get_text(strip=True)
                siblings = td.find_next_siblings("td")
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

        for label in ["Quality", "Potential", "Affected Quality"]:
            if label not in data:
                b_tag = soup.find("b", string=label)
                if b_tag:
                    parent = b_tag.find_parent("td")
                    if parent:
                        for sib in parent.find_next_siblings("td"):
                            txt = sib.get_text(strip=True)
                            if txt:
                                data[label] = txt
                                break

        return data

    def get_player_history(self, player_id: str) -> float:
        """Scrape the most recent transfer price from the player's history page.

        Args:
            player_id: Numeric player ID string from PManager.

        Returns:
            Most recent transfer price as a float, or ``0.0`` if not found.
        """
        history_url = f"{self.base_url}/marcos_jog.asp?jog_id={player_id}"
        logger.debug("Checking history for %s...", player_id)

        try:
            self.page.goto(history_url)
            try:
                self.page.wait_for_selector("div#tabela_titulo", timeout=3000)
            except Exception as e:
                logger.debug("Timeout waiting for history page (%s): %s", player_id, e)

            soup = BeautifulSoup(self.page.content(), "html.parser")

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
                        cols = rows[0].find_all("td")
                        if len(cols) >= 4:
                            return clean_currency(cols[3].get_text(strip=True))

        except Exception as e:
            logger.error("Error scraping history for %s: %s", player_id, e, exc_info=True)

        return 0.0

    def get_bid_info(self, player_id: str) -> dict[str, Any]:
        """Quickly fetch current bid and listing data for a player.

        Args:
            player_id: Numeric player ID string from PManager.

        Returns:
            Dictionary with keys: ``estimated_value``, ``bids_count``,
            ``bids_avg``, ``deadline``.
        """
        neg_url = f"{self.base_url}/comprar_jog_lista.asp?jg_id={player_id}"
        data: dict[str, Any] = {
            "estimated_value": 0,
            "bids_count": 0,
            "bids_avg": "0",
            "deadline": "N/A",
        }

        try:
            self.page.goto(neg_url)
            try:
                self.page.wait_for_selector("body", timeout=3000)
            except Exception as e:
                logger.debug("Timeout waiting for bid page (%s): %s", player_id, e)

            soup = BeautifulSoup(self.page.content(), "html.parser")

            data["estimated_value"] = self._get_val(soup, "Estimated Transfer Value") or 0

            dl = soup.find(string="Deadline")
            if dl:
                parent = dl.find_parent("td")
                if parent:
                    val_td = parent.find_next_sibling("td")
                    if val_td:
                        data["deadline"] = val_td.get_text(strip=True, separator=" ")

            bids = soup.find(string="Bids")
            if bids:
                parent = bids.find_parent("td")
                if parent:
                    val_td = parent.find_next_sibling("td")
                    if val_td:
                        txt = val_td.get_text(strip=True)
                        if txt.isdigit():
                            data["bids_count"] = int(txt)

            bavg = soup.find(string="Bids Average (Scout)")
            if bavg:
                parent = bavg.find_parent("td")
                if parent:
                    val_td = parent.find_next_sibling("td")
                    if val_td:
                        data["bids_avg"] = val_td.get_text(strip=True)

        except Exception as e:
            logger.error("Error scraping bid info for %s: %s", player_id, e, exc_info=True)

        return data
