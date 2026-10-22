"""
Unit tests for src.core.report_html — the redesigned relatorio.asp page (no pm-match-report JSON).
"""

from bs4 import BeautifulSoup

from src.core.report_html import match_from_html


def _player(jog: int, x: int, y: int, name: str, gk: bool = False, rating: str = "7,0") -> str:
    cls = "mr-pp mr-pp--gk" if gk else "mr-pp"
    return (
        f'<div data-jog="{jog}" class="{cls}" style="left: {x}%; top: {y}%; --x: {x}%; --y: {y}%;">'
        f'<span class="mr-pp__rating">{rating}</span>'
        f'<a class="mr-pp__name" title="{name}" href="ver_jogador.asp?jog_id={jog}">{name.split()[-1]}</a></div>'
    )


def _side(first_id: int, mirror: bool) -> str:
    # GK, 4 defenders, 3 midfielders, 3 forwards; --x is the distance from the home goal
    xs = [5, 16, 16, 17, 16, 28, 30, 28, 42, 42, 42]
    out = []
    for i, x in enumerate(xs):
        out.append(_player(first_id + i, 100 - x if mirror else x, 20 + 5 * i, f"Player {first_id + i}", gk=i == 0))
    return "".join(out)


PAGE = f"""
<div class="rh"><div class="rh-board">
  <a class="rh-team__name" href="ver_equipa.asp?equipa=111">Home FC</a>
  <a class="rh-team__name" href="ver_equipa.asp?equipa=222">Away FC</a>
  <div class="rh-board__meta"><span title="Match Type">League (Serbia) - Prva Liga, 9 round</span>
  <span title="Date">22/10/2026</span></div>
  <div class="rh-events"><div class="rh-events__col rh-events__col--home"></div>
  <div class="rh-events__col rh-events__col--away">
    <div class="rh-ev rh-ev--g"><span class="rh-ev__txt"><a href="ver_jogador.asp?jog_id=2010">Player 2010</a>
      <span class="rh-ev__min">20', 32'</span></span></div>
    <div class="rh-ev rh-ev--y"><span class="rh-ev__txt"><a href="ver_jogador.asp?jog_id=2005">Player 2005</a>
      <span class="rh-ev__min">83'</span></span></div>
  </div></div>
</div></div>
<table><tr><td class="cabecalhos">Formation</td><td><div class="comentarios">4-3-3_v3</div></td><td></td>
<td><div class="comentarios">4-3-3_v3</div></td></tr></table>
<div class="mr-pitch">{_side(1000, False)}{_side(2000, True)}</div>
<div class="mr-sub" data-jog="1500" data-out="h10"><span class="mr-sub__title"><span class="mr-sub__in">↑ 60'</span>
 <a href="ver_jogador.asp?jog_id=1500">Sub Home</a></span>
 <span class="mr-sub__out"><a href="ver_jogador.asp?jog_id=1010">Player 1010</a></span></div>
"""


class TestMatchFromHtml:
    def setup_method(self) -> None:
        self.match = match_from_html(BeautifulSoup(PAGE, "html.parser"))

    def test_teams_and_date(self) -> None:
        assert self.match["homeTeam"] == {"id": 111, "name": "Home FC"}
        assert self.match["awayTeam"] == {"id": 222, "name": "Away FC"}
        assert self.match["info"]["date"] == "2026-10-22T00:00:00Z"

    def test_events_have_team_player_and_every_minute(self) -> None:
        goals = [e for e in self.match["events"] if e["typeId"] == 7]
        assert [(g["timeInMinutes"], g["playerId"], g["teamId"]) for g in goals] == [(20, 2010, 222), (32, 2010, 222)]
        assert [e["typeId"] for e in self.match["events"] if e["typeId"] != 7] == [1]

    def test_lineup_lines_follow_the_formation(self) -> None:
        for key, first in (("homeFormation", 1000), ("awayFormation", 2000)):
            xi = self.match[key]["startingEleven"]
            assert len(xi) == 11 and xi[0]["playerId"] == first
            assert [p["positionType"] for p in xi] == [0, 1, 1, 1, 1, 2, 2, 2, 3, 3, 3]

    def test_substitution_names_the_player_leaving(self) -> None:
        sub = self.match["homeFormation"]["substitutions"][0]
        assert sub["playerId"] == 1500 and sub["subIn"] == {"playerId": 1010, "playerName": "Player 1010", "minute": 60}
        assert self.match["awayFormation"]["substitutions"] == []

    def test_page_without_a_pitch_has_no_match(self) -> None:
        assert match_from_html(BeautifulSoup("<div>2D viewer</div>", "html.parser")) is None
