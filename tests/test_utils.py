"""
Unit tests for src.core.utils — clean_currency() and parse_deadline().
"""

from datetime import date, datetime, timedelta, timezone

import pytest

from bs4 import BeautifulSoup

from src.core.utils import clean_currency, parse_deadline, parse_skill_flags


class TestCleanCurrency:
    """Tests for clean_currency()."""

    def test_comma_separated(self) -> None:
        assert clean_currency("1,234,567") == 1_234_567.0

    def test_dot_separated(self) -> None:
        """European-style thousand-separator (dots)."""
        assert clean_currency("1.234.567") == 1_234_567.0

    def test_with_dollar_sign(self) -> None:
        assert clean_currency("$500,000") == 500_000.0

    def test_plain_integer_string(self) -> None:
        assert clean_currency("1500") == 1_500.0

    def test_float_string(self) -> None:
        assert clean_currency("1500.50") == 150_050.0  # strips dot, treats as digits

    def test_none_returns_zero(self) -> None:
        assert clean_currency(None) == 0.0

    def test_empty_string_returns_zero(self) -> None:
        assert clean_currency("") == 0.0

    def test_whitespace_only_returns_zero(self) -> None:
        assert clean_currency("   ") == 0.0

    def test_non_numeric_string_returns_zero(self) -> None:
        assert clean_currency("N/A") == 0.0

    def test_with_currency_label(self) -> None:
        """Game appends ' baht' to amounts."""
        assert clean_currency("5.264.850 baht") == 5_264_850.0

    def test_integer_input_coerced(self) -> None:
        assert clean_currency(1_000_000) == 1_000_000.0  # type: ignore[arg-type]


class TestParseDeadline:
    """Tests for parse_deadline()."""

    def test_today_deadline(self) -> None:
        _BKK = timezone(timedelta(hours=7))
        today_bkk = datetime.now(tz=_BKK).date()
        result = parse_deadline("Today at 14:30")
        assert result is not None
        assert result.hour == 14
        assert result.minute == 30
        assert result.date() == today_bkk

    def test_tomorrow_deadline(self) -> None:
        _BKK = timezone(timedelta(hours=7))
        tomorrow_bkk = datetime.now(tz=_BKK).date() + timedelta(days=1)
        result = parse_deadline("Tomorrow at 08:00")
        assert result is not None
        assert result.hour == 8
        assert result.minute == 0
        assert result.date() == tomorrow_bkk

    def test_case_insensitive(self) -> None:
        result = parse_deadline("TODAY AT 10:00")
        assert result is not None
        assert result.hour == 10

    def test_none_input_returns_none(self) -> None:
        assert parse_deadline(None) is None

    def test_empty_string_returns_none(self) -> None:
        assert parse_deadline("") is None

    def test_unrecognised_string_returns_none(self) -> None:
        assert parse_deadline("Next week") is None

    def test_string_without_time_returns_none(self) -> None:
        assert parse_deadline("Tomorrow") is None

    def test_midnight_time(self) -> None:
        result = parse_deadline("Today at 00:00")
        assert result is not None
        assert result.hour == 0
        assert result.minute == 0

    def test_result_is_offset_from_utc(self) -> None:
        """Result should be UTC+7, so hour matches the string exactly."""
        result = parse_deadline("Today at 15:45")
        assert result is not None
        assert result.hour == 15
        assert result.minute == 45


def _skill_row(name: str, value: str, color: str) -> str:
    # Trimmed from a real ver_jogador.asp skill row.
    return (
        f'<tr><td class="list1"><b>{name}</b></td><td class="list1"><img src="img/bluebar.png"></td>'
        f'<td class="list1" align="center">{value}</td>'
        f'<td class="list1"><div class="team_players"><font color="{color}">World Class</font></div></td></tr>'
    )


class TestParseSkillFlags:
    """Tests for parse_skill_flags()."""

    def test_colours_map_to_flags(self) -> None:
        html = "<table>" + "".join([
            '<tr><td class="team_players"><b>Value</b></td><td>&nbsp;</td>'
            '<td class="team_players">66.739.400 baht</td><td colspan="4">&nbsp;</td></tr>',
            _skill_row("Passing", "20", "blue"),
            _skill_row("Positioning", "20", ""),
            _skill_row("Tackling", "15", "green"),
            _skill_row("Speed", "6", "red"),
        ]) + "</table>"
        flags = parse_skill_flags(BeautifulSoup(html, "html.parser"))
        assert flags == {"Passing": "max", "Tackling": "up", "Speed": "down"}

    def test_no_skills_visible(self) -> None:
        assert parse_skill_flags(BeautifulSoup("<table><tr><td>?</td></tr></table>", "html.parser")) == {}
