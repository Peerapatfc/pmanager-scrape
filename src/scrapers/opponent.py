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

    def get_team_players(self, team_url: str) -> tuple[str | None, list[str]]:
        """Extract the team name and all player IDs from an opponent team's squad page.

        Args:
            team_url: Full URL of the team page (e.g.
                ``https://www.pmanager.org/ver_equipa.asp?equipa=12345``).

        Returns:
            A tuple of ``(team_name, player_ids)`` where ``team_name`` may be
            ``None`` if it cannot be determined from the page.
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

        player_ids: list[str] = []
        rows = roster_soup.find_all("tr", class_=["list1", "list2"])
        logger.info("Found %d rows in squad table.", len(rows))

        for row in rows:
            link = row.find("a", href=re.compile(r"ver_jogador\.asp\?jog_id=\d+"))
            if link:
                href = link["href"]
                try:
                    pid = href.split("jog_id=")[-1]
                    player_ids.append(pid)
                except IndexError:
                    continue

        unique_ids = list(set(player_ids))
        logger.info("Found %d unique players in team.", len(unique_ids))
        return team_name, unique_ids
