"""
Opponent team scraper for PManager.org.

Extracts all player IDs from a given opponent team page so that their
profiles can be analysed for scouting purposes.
"""

import re

from bs4 import BeautifulSoup

from src.core.logger import logger
from src.scrapers.base import BaseScraper


class OpponentScraper(BaseScraper):
    """Scrapes the squad listing of an opponent team page."""

    def get_team_players(self, team_url: str) -> tuple[str | None, list[dict]]:
        """Extract the team name and all player data from an opponent team's squad page.

        Args:
            team_url: Full URL of the team page (e.g.
                ``https://www.pmanager.org/ver_equipa.asp?equipa=12345``).

        Returns:
            A tuple of ``(team_name, players)`` where ``team_name`` may be
            ``None`` if it cannot be determined from the page, and ``players``
            is a list of dicts with keys: player_id, name, age, position, quality.
        """
        # The roster URL uses vjog=1 which renders only the player list — the
        # General Info table (where the team name lives) only appears on the
        # plain team page.  Load the info page first, then the roster page.
        info_url = re.sub(r"[&?]vjog=1", "", team_url)

        logger.info("Navigating to team info page: %s", info_url)
        self.page.goto(info_url)
        self.page.wait_for_load_state("networkidle")

        info_soup = BeautifulSoup(self.page.content(), "html.parser")

        # Extract team name from the General Info table.
        # Two observed structures:
        #   A) <font size="+1"><b>BlueStar06</b> (<b>35859</b>)</font>
        #   B) <font size="+1">F_ck Alex</font>(<b>38349</b>)
        # Read font tag text and strip any trailing " (numeric_id)".
        team_name: str | None = None
        for label_td in info_soup.find_all("td", class_="comentarios"):
            if "name" in label_td.get_text(strip=True).lower():
                value_td = label_td.find_next_sibling("td")
                if value_td:
                    font_tag = value_td.find("font")
                    if font_tag:
                        raw = font_tag.get_text(strip=True)
                        team_name = re.sub(r"\s*\(\d+\)\s*$", "", raw).strip() or None
                break

        if team_name:
            logger.info("Team name: %s", team_name)
        else:
            logger.warning("Could not extract team name from General Info table.")

        logger.info("Navigating to team roster page: %s", team_url)
        self.page.goto(team_url)
        self.page.wait_for_load_state("networkidle")

        roster_soup = BeautifulSoup(self.page.content(), "html.parser")

        players: list[dict] = []
        seen_ids: set[str] = set()
        rows = roster_soup.find_all("tr", class_=["list1", "list2"])
        logger.info("Found %d rows in squad table.", len(rows))

        # Fallback: some team pages use different row classes. Walk up from
        # each player link to its parent <tr> instead.
        if not rows:
            logger.info("No list1/list2 rows found — falling back to link-based detection.")
            all_links = roster_soup.find_all("a", href=re.compile(r"ver_jogador\.asp\?jog_id=\d+"))
            rows = []
            for lnk in all_links:
                parent_tr = lnk.find_parent("tr")
                if parent_tr and parent_tr not in rows:
                    rows.append(parent_tr)
            logger.info("Fallback found %d rows via player links.", len(rows))

        for row in rows:
            link = row.find("a", href=re.compile(r"ver_jogador\.asp\?jog_id=\d+"))
            if not link:
                continue
            href = link["href"]
            try:
                pid = href.split("jog_id=")[-1]
            except IndexError:
                continue
            if pid in seen_ids:
                continue
            seen_ids.add(pid)

            name = link.get_text(strip=True)

            tds = row.find_all("td")
            if len(tds) >= 12:
                # Position is in td[1]; use separator to preserve space between
                # tag text and adjacent text (e.g. <b>D</b> RLC → "D RLC")
                pos_raw = tds[1].get_text(separator=" ", strip=True)
                position = " ".join(pos_raw.split())

                age_raw = tds[3].get_text(strip=True)
                try:
                    age = int(age_raw)
                except (ValueError, TypeError):
                    age = 0

                # Quality text follows the bar images in td[11]
                quality = tds[11].get_text(strip=True)
            else:
                position = ""
                age = 0
                quality = ""

            players.append({
                "player_id": pid,
                "name": name,
                "age": age,
                "position": position,
                "quality": quality,
            })

        logger.info("Found %d unique players in team.", len(players))
        return team_name, players

    def get_player_skills(self, player_id: str, base_url: str) -> dict:
        """Scrape skill attributes from a player's profile page.

        Args:
            player_id: Numeric player ID string from PManager.
            base_url: Base URL of PManager (e.g. ``https://www.pmanager.org``).

        Returns:
            Dict with keys ``id`` and any skill names found (e.g. ``Speed``,
            ``Finishing``). Unknown skill names are preserved as-is so that
            ``SupabaseManager.upsert_players`` can pack them into the
            ``skills`` JSONB column automatically.
        """
        prof_url = f"{base_url}/ver_jogador.asp?jog_id={player_id}"
        self.page.goto(prof_url)
        try:
            self.page.wait_for_selector("div#infos", timeout=5000)
        except Exception as e:
            logger.debug("Timeout waiting for div#infos (%s): %s", player_id, e)

        soup = BeautifulSoup(self.page.content(), "html.parser")
        data: dict = {"id": player_id}

        # Extract skill rows from the profile table (same pattern as TransferScraper)
        for td in soup.find_all("td", class_=["list1", "list2"]):
            b_tag = td.find("b")
            if not b_tag:
                continue
            skill_name = b_tag.get_text(strip=True)
            for sib in td.find_next_siblings("td"):
                text = sib.get_text(strip=True)
                if text.isdigit():
                    data[skill_name] = int(text)
                    break
                if text and ("Fit" in text or "%" in text):
                    data[skill_name] = text
                    break

        logger.debug("Scraped %d skill keys for player %s", len(data) - 1, player_id)
        return data
