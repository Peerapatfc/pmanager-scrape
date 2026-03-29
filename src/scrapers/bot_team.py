"""
BOT team discovery and player evaluation scraper.

Traverses all countries and league divisions in PManager to identify
AI-controlled (BOT) teams, then evaluates each team's roster to find
undervalued players worth targeting.
"""

import re
from typing import Any

from bs4 import BeautifulSoup

from src import constants
from src.core.logger import logger
from src.core.utils import clean_currency
from src.scrapers.base import BaseScraper


class BotTeamScraper(BaseScraper):
    """Discovers BOT teams across all leagues and evaluates their players."""

    def __init__(self, base_url: str = "https://www.pmanager.org") -> None:
        """Initialise the scraper.

        Args:
            base_url: Root URL of the PManager site.
        """
        super().__init__(base_url=base_url)
        self.accepted_qualities: tuple[str, ...] = constants.BOT_ACCEPTED_QUALITIES

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_prof_info(self, soup: BeautifulSoup, label: str) -> str:
        """Extract a profile attribute value that follows a bold label.

        Args:
            soup: Parsed profile page HTML.
            label: Exact text content of the ``<b>`` label tag to locate.

        Returns:
            First non-empty sibling cell text, or ``"N/A"`` if not found.
        """
        b_tag = soup.find("b", string=label)
        if b_tag:
            parent = b_tag.find_parent("td")
            if parent:
                for sib in parent.find_next_siblings("td"):
                    txt = sib.get_text(strip=True)
                    if txt:
                        return txt
        return "N/A"

    def _get_neg_val(self, soup: BeautifulSoup, label: str) -> float:
        """Extract a currency value from the negotiation page.

        Args:
            soup: Parsed negotiation page HTML.
            label: Regex-compatible label string to locate.

        Returns:
            Parsed currency value as a float, or ``0.0`` if not found.
        """
        node = soup.find(string=re.compile(label))
        if node:
            parent = node.find_parent("td")
            if parent:
                val_td = parent.find_next_sibling("td")
                if val_td:
                    return clean_currency(val_td.get_text(strip=True))
        return 0.0

    # ------------------------------------------------------------------
    # Country / league traversal
    # ------------------------------------------------------------------

    def get_all_countries(self) -> list[dict[str, str]]:
        """Extract all active countries from the sidebar dropdown.

        Returns:
            List of dicts with ``"id"`` and ``"name"`` keys.
        """
        self.page.goto(f"{self.base_url}/ver_mundo.asp")
        try:
            self.page.wait_for_selector("#countryList", timeout=5000)
        except Exception as e:
            logger.warning(
                "Could not find #countryList dropdown on ver_mundo.asp: %s", e
            )

        soup = BeautifulSoup(self.page.content(), "html.parser")
        country_select = soup.find("select", id="countryList")

        countries: list[dict[str, str]] = []
        if country_select:
            for option in country_select.find_all("option"):
                val = option.get("value")
                name = option.get_text(strip=True)
                if val and name:
                    countries.append({"id": val, "name": name})

        return countries

    def scrape_league_tree(
        self, max_division: int = constants.MAX_DIVISION
    ) -> list[dict[str, str]]:
        """Traverse all countries and their divisions to collect BOT teams.

        Args:
            max_division: Stop descending into divisions deeper than this
                number. Defaults to :data:`~src.constants.MAX_DIVISION`.

        Returns:
            Deduplicated list of BOT team dicts with keys ``id``, ``name``,
            ``country``, and ``division``.
        """
        countries = self.get_all_countries()
        if not countries:
            logger.warning("No countries found from dropdown.")
            return []

        all_bot_teams: list[dict[str, str]] = []

        for country in countries:
            cid = country["id"]
            cname = country["name"]
            logger.info("--- Scraping Country: %s (ID: %s) ---", cname, cid)

            self.page.goto(f"{self.base_url}/ver_pais.asp?nm=1&id={cid}")
            soup_pais = BeautifulSoup(self.page.content(), "html.parser")
            sg_val = None
            league_link = soup_pais.find(
                "a", href=re.compile(r"classificacao\.asp\?.*sg=", re.IGNORECASE)
            )
            if league_link:
                sg_match = re.search(r"sg=([A-Z0-9]+)", league_link["href"], re.IGNORECASE)
                if sg_match:
                    sg_val = sg_match.group(1)

            if not sg_val:
                logger.warning(
                    "Could not resolve sg= parameter for %s. Skipping.", cname
                )
                continue

            logger.info("Resolved %s -> sg=%s", cname, sg_val)
            current_league_url = (
                f"{self.base_url}/classificacao.asp?dv=1&sr=1&vf=1&sg={sg_val}"
            )

            while current_league_url:
                teams, next_url = self.get_bot_teams_and_next_league(
                    cname, current_league_url
                )
                if teams:
                    all_bot_teams.extend(teams)

                if next_url:
                    if max_division is not None:
                        dv_match = re.search(r"dv=(\d+)", next_url)
                        if dv_match and int(dv_match.group(1)) > max_division:
                            break
                    current_league_url = (
                        next_url
                        if next_url.startswith("http")
                        else f"{self.base_url}/{next_url}"
                    )
                else:
                    break

        # Deduplicate by team ID
        unique_bots = {t["id"]: t for t in all_bot_teams}.values()
        return list(unique_bots)

    def get_bot_teams_and_next_league(
        self, country_name: str, url: str
    ) -> tuple[list[dict[str, str]], str | None]:
        """Extract BOT teams from a single league table page.

        BOT teams are identified by the absence of bold formatting on their
        name link (human-managed teams are displayed in bold).

        Args:
            country_name: Display name of the country being scraped (for logs).
            url: Full URL of the league standings page.

        Returns:
            Tuple of ``(bot_teams, next_league_url)`` where ``bot_teams`` is a
            list of dicts and ``next_league_url`` is the URL of the next series
            or division to follow (or ``None`` if there is none).
        """
        self.page.goto(url)
        try:
            self.page.wait_for_selector("table", timeout=3000)
        except Exception as e:
            logger.debug("Timeout waiting for league table at %s: %s", url, e)

        soup = BeautifulSoup(self.page.content(), "html.parser")

        dv_match = re.search(r"dv=(\d+)", url)
        sr_match = re.search(r"sr=(\d+)", url)
        dv = dv_match.group(1) if dv_match else "Unknown"
        sr = sr_match.group(1) if sr_match else "1"

        bot_teams: list[dict[str, str]] = []

        league_table = None
        for table in soup.find_all("table"):
            if table.find(lambda t: t.name in ["td", "th"] and "Position" in t.text):
                league_table = table
                break
        if not league_table:
            league_table = soup

        links = league_table.find_all(
            "a",
            href=re.compile(
                r"(clube\.asp\?clube=|ver_equipa\.asp\?equipa=)\d+", re.IGNORECASE
            ),
        )

        seen_teams: set[str] = set()
        for a in links:
            team_id_match = re.search(r"(?:clube=|equipa=)(\d+)", a["href"], re.IGNORECASE)
            if not team_id_match:
                continue
            team_id = team_id_match.group(1)
            if team_id in seen_teams:
                continue

            seen_teams.add(team_id)
            team_name = a.get_text(strip=True)
            is_bold = (a.find(["b", "strong"]) is not None) or (
                a.find_parent(["b", "strong"]) is not None
            )

            if not is_bold:
                bot_teams.append(
                    {
                        "id": team_id,
                        "name": team_name,
                        "country": country_name,
                        "division": dv,
                    }
                )

        next_league_url: str | None = None
        for img in soup.find_all("img"):
            src = img.get("src", "").lower()
            if "fs_arrow_right.gif" in src:
                parent_a = img.find_parent("a")
                if parent_a and parent_a.get("href"):
                    next_league_url = parent_a["href"]
                    break

        if not next_league_url:
            for img in soup.find_all("img"):
                src = img.get("src", "").lower()
                if "fs_arrow_down.gif" in src:
                    parent_a = img.find_parent("a")
                    if parent_a and parent_a.get("href"):
                        next_league_url = parent_a["href"]
                        break

        logger.info(
            "[%s D%sS%s] Found %d bot teams. Next URL: %s",
            country_name,
            dv,
            sr,
            len(bot_teams),
            next_league_url,
        )
        return bot_teams, next_league_url

    # ------------------------------------------------------------------
    # Team roster & player evaluation
    # ------------------------------------------------------------------

    def get_team_roster(self, team_id: str) -> list[str]:
        """Extract player IDs from a team's roster page.

        Args:
            team_id: Numeric team ID string from PManager.

        Returns:
            Deduplicated list of player ID strings.
        """
        url = f"{self.base_url}/ver_equipa.asp?equipa={team_id}&vjog=1"
        self.page.goto(url)
        try:
            self.page.wait_for_selector("table", timeout=3000)
        except Exception as e:
            logger.debug("Timeout waiting for team roster (%s): %s", team_id, e)

        soup = BeautifulSoup(self.page.content(), "html.parser")

        player_ids: list[str] = []
        links = soup.find_all("a", href=re.compile(r"ver_jogador\.asp\?jog_id=\d+"))
        for a in links:
            pid_match = re.search(r"jog_id=(\d+)", a["href"])
            if pid_match:
                player_ids.append(pid_match.group(1))

        return list(set(player_ids))

    def evaluate_player(
        self, player_id: str, team_name: str
    ) -> dict[str, Any] | None:
        """Evaluate a single BOT player and return opportunity data.

        Visits the negotiation page for financials and the profile page for
        attributes. Returns ``None`` if either page fails to load.

        Args:
            player_id: Numeric player ID string from PManager.
            team_name: Display name of the owning BOT team.

        Returns:
            Dictionary with opportunity fields, or ``None`` on failure.
        """
        # --- Negotiation Page (Financials) ---
        neg_url = f"{self.base_url}/comprar_jog_lista.asp?jg_id={player_id}"
        self.page.goto(neg_url)
        try:
            self.page.wait_for_selector("body", timeout=3000)
        except Exception as e:
            logger.debug("Timeout on negotiation page (%s): %s", player_id, e)

        soup_neg = BeautifulSoup(self.page.content(), "html.parser")

        try:
            estimated_value = self._get_neg_val(soup_neg, "Estimated Transfer Value")
            asking_price = self._get_neg_val(soup_neg, "Asking Price")
        except Exception as e:
            logger.error("Error extracting financials for %s: %s", player_id, e, exc_info=True)
            return None

        # --- Profile Page (Attributes) ---
        prof_url = f"{self.base_url}/ver_jogador.asp?jog_id={player_id}"
        self.page.goto(prof_url)
        try:
            self.page.wait_for_selector("body", timeout=3000)
        except Exception as e:
            logger.debug("Timeout on profile page (%s): %s", player_id, e)

        soup_prof = BeautifulSoup(self.page.content(), "html.parser")

        try:
            name_font = soup_prof.find("font", size="+1")
            name = name_font.get_text(strip=True) if name_font else "Unknown"

            quality = self._get_prof_info(soup_prof, "Quality")
            position = self._get_prof_info(soup_prof, "Position")
            age_raw = self._get_prof_info(soup_prof, "Age")
            age = 0
            if age_raw and "Years" in age_raw:
                try:
                    age = int(age_raw.replace("Years", "").strip())
                except ValueError:
                    age = 0

        except Exception as e:
            logger.error("Error extracting profile for %s: %s", player_id, e, exc_info=True)
            return None

        value_diff = estimated_value - asking_price
        profit_margin = 0.0
        if asking_price > 0:
            profit_margin = round((value_diff / asking_price) * 100, 2)

        logger.info(
            "Target Found! %s (%s) - Price: %s, Est: %s",
            name,
            quality,
            asking_price,
            estimated_value,
        )

        return {
            "id": player_id,
            "name": name,
            "position": position,
            "age": age,
            "quality": quality,
            "team_name": team_name,
            "estimated_value": estimated_value,
            "asking_price": asking_price,
            "value_diff": value_diff,
            "profit_margin": profit_margin,
            "url": prof_url,
        }
