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
        logger.info("Navigating to team page: %s", team_url)
        self.page.goto(team_url)
        self.page.wait_for_load_state("networkidle")

        content = self.page.content()
        soup = BeautifulSoup(content, "html.parser")

        # Extract team name from the page <title>, which follows the pattern
        # "Team Name | PManager.org" or "Team Name - PManager.org"
        team_name: str | None = None
        title_tag = soup.find("title")
        if title_tag:
            raw = title_tag.get_text(strip=True)
            for sep in [" | ", " - ", " – "]:
                if sep in raw:
                    team_name = raw.split(sep)[0].strip() or None
                    break

        if team_name:
            logger.info("Team name: %s", team_name)
        else:
            logger.warning("Could not extract team name from page title.")

        player_ids: list[str] = []
        rows = soup.find_all("tr", class_=["list1", "list2"])
        logger.info("Found %d rows in squad table.", len(rows))

        for row in rows:
            link = row.find("a", href=re.compile(r"ver_jogador\.asp\?jog_id="))
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
