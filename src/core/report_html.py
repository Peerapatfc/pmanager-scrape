"""
Match report data read from the HTML of ``relatorio.asp``.

The old report page embedded the whole match as a ``pm-match-report`` JSON blob. The
redesigned page has no JSON, so :func:`match_from_html` rebuilds the same ``match``
dict (teams, date, lineups, substitutions, goal / card events) from the markup:

- team links ``a.rh-team__name`` (home first) and the meta spans titled ``Date`` / ``Match Type``;
- the 22 players on the pitch ``.mr-pitch .mr-pp`` (home side first, goalkeeper first in each
  side, ``--x`` = distance from the home goal so the away side is mirrored);
- substitutions ``.mr-sub`` (``data-jog`` = player coming on, ``data-out`` = ``h``/``a`` + slot,
  the link in ``.mr-sub__out`` = player leaving);
- events under the scoreboard ``.rh-events__col--home|away .rh-ev`` (class ``rh-ev--g`` goal,
  ``y`` yellow, ``r`` red, ``i`` injury; several minutes may share a line).

While a match is on the header lists no events, so goals are then read from the Comments feed
(``li.rf-item--goal``, new score in ``.rf-pill``); those goals carry no player.
"""

import re
from typing import Any

from bs4 import BeautifulSoup

#: typeId used by the old JSON for each ``rh-ev--*`` class.
EVENT_TYPE: dict[str, int] = {"g": 7, "y": 1, "r": 2, "i": 6, "inj": 6}


def _int(value: str | None) -> int | None:
    return int(value) if value and value.isdigit() else None


def _jog_id(tag: Any) -> int | None:
    href = tag.get("href", "") if tag else ""
    m = re.search(r"jog_id=(\d+)", href)
    return int(m.group(1)) if m else None


def _team(link: Any, own_id: int | None) -> dict[str, Any]:
    m = re.search(r"equipa=(\d+)", link.get("href", ""))
    return {"id": int(m.group(1)) if m else own_id, "name": link.get_text(strip=True)}


def _pitch_x(player: Any) -> float:
    m = re.search(r"--x:\s*([\d.]+)%", player.get("style", ""))
    return float(m.group(1)) if m else 0.0


def _formation(soup: BeautifulSoup, side: int, col: int, players: list[Any]) -> dict[str, list]:
    """One side's lineup and substitutions (``side`` 0 = home, 1 = away; ``col`` = cell in the Formation row)."""
    row = next(
        (tr for tr in soup.find_all("tr") if tr.find("td") and tr.find("td").get_text(strip=True) == "Formation"),
        None,
    )
    cells = row.find_all("td", recursive=False) if row else []
    shape = re.match(r"\s*(\d)-(\d)-(\d)", cells[col].get_text(strip=True)) if len(cells) > col else None

    mine = players[side * 11 : side * 11 + 11]
    keeper = next((p for p in mine if "mr-pp--gk" in p.get("class", [])), mine[0])
    line_of = {id(keeper): 0}
    field = sorted((p for p in mine if p is not keeper), key=lambda p: 100 - _pitch_x(p) if side else _pitch_x(p))
    start = 0
    counts = [int(n) for n in shape.groups()] if shape else []
    for line, count in enumerate(counts):
        for p in field[start : start + count]:
            line_of[id(p)] = line + 1
        start += count

    key = "a" if side else "h"
    subs = []
    for s in soup.select(".mr-sub"):
        if not s.get("data-out", "").startswith(key):
            continue
        name = s.select_one(".mr-sub__title a")
        out = s.select_one(".mr-sub__out a")
        minute = re.search(r"\d+", s.select_one(".mr-sub__in").get_text() if s.select_one(".mr-sub__in") else "")
        subs.append({
            "playerId": _int(s.get("data-jog")),
            "playerName": name.get_text(strip=True) if name else "",
            "subIn": {
                "playerId": _jog_id(out),
                "playerName": out.get_text(strip=True) if out else "",
                "minute": int(minute.group()) if minute else None,
            },
        })
    return {
        "startingEleven": [
            {
                "playerId": _int(p.get("data-jog")),
                "playerName": (p.select_one(".mr-pp__name") or {}).get("title", "").strip(),
                "positionType": line_of.get(id(p)),
            }
            for p in mine
        ],
        "substitutions": subs,
    }


def match_from_html(soup: BeautifulSoup) -> dict[str, Any] | None:
    """Rebuild the old ``match`` dict from a report page, or ``None`` when the page has no match data.

    Returns:
        ``{"homeTeam", "awayTeam", "info": {"date"}, "events", "homeFormation", "awayFormation"}``
        shaped like the old JSON (ids are ints, ``info.date`` is ``YYYY-MM-DDT00:00:00Z``).
    """
    links = soup.select("a.rh-team__name")[:2]
    players = soup.select(".mr-pitch .mr-pp")
    if len(links) < 2 or len(players) != 22:
        return None

    own = soup.find("a", href=re.compile(r"mudar\.asp\?action=6&id=\d+"))
    own_id = int(re.search(r"id=(\d+)", own["href"]).group(1)) if own else None
    home, away = _team(links[0], own_id), _team(links[1], own_id)

    date_span = soup.find("span", attrs={"title": "Date"})
    d = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", date_span.get_text() if date_span else "")
    date = f"{d.group(3)}-{int(d.group(2)):02d}-{int(d.group(1)):02d}T00:00:00Z" if d else ""

    events: list[dict[str, Any]] = []
    for col, team in (("home", home), ("away", away)):
        for ev in soup.select(f".rh-events__col--{col} .rh-ev"):
            kind = next((c[len("rh-ev--"):] for c in ev.get("class", []) if c.startswith("rh-ev--")), "")
            minutes = ev.select_one(".rh-ev__min")
            for m in re.findall(r"\d+", minutes.get_text() if minutes else ""):
                events.append({
                    "typeId": EVENT_TYPE.get(kind, -1),
                    "timeInMinutes": int(m),
                    "playerId": _jog_id(ev.find("a")),
                    "teamId": team["id"],
                })
    if not events:  # a match in progress: goals only, from the commentary feed (the score says who scored)
        goals = []
        for li in soup.select("li.rf-item--goal"):
            score = re.search(r"(\d+)\s*-\s*(\d+)", (li.select_one(".rf-pill") or li).get_text())
            minute = re.search(r"\d+", (li.select_one(".rf-min") or li).get_text())
            if score and minute:
                goals.append((int(score.group(1)) + int(score.group(2)), int(minute.group()), int(score.group(1))))
        prev_home = 0
        for _, minute, home_goals in sorted(goals):
            events.append({
                "typeId": 7, "timeInMinutes": minute, "playerId": None,
                "teamId": home["id"] if home_goals > prev_home else away["id"],
            })
            prev_home = home_goals

    return {
        "homeTeam": home,
        "awayTeam": away,
        "info": {"date": date},
        "events": events,
        "homeFormation": _formation(soup, 0, 1, players),
        "awayFormation": _formation(soup, 1, 3, players),
    }
