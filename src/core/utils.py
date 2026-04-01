"""
Shared utility functions for pmanager-scrape.

Provides helpers for parsing game-specific data formats (currency strings,
auction deadlines) that are used across multiple scrapers and entry scripts.
"""

import re
from datetime import datetime, timedelta, timezone


def parse_deadline(deadline_str: str | None) -> datetime | None:
    """Parse a game deadline string into a timezone-aware datetime.

    The game displays deadlines as ``"Today at 10:19"`` or
    ``"Tomorrow at 08:00"``. This function converts them to an absolute
    ``datetime`` in the local server timezone (UTC+7).

    Args:
        deadline_str: Raw deadline text scraped from the game page, e.g.
            ``"Today at 14:30"`` or ``"Tomorrow at 08:00"``. Pass ``None``
            or an empty string to get ``None`` back.

    Returns:
        A :class:`~datetime.datetime` object in UTC+7, or ``None`` if the
        string cannot be parsed.

    Examples:
        >>> parse_deadline("Today at 14:30")
        datetime(...)  # today's date at 14:30 UTC+7
        >>> parse_deadline(None)
        None
    """
    if not deadline_str or not isinstance(deadline_str, str):
        return None

    txt = deadline_str.strip()
    time_match = re.search(r"(\d{1,2}):(\d{2})", txt)
    if not time_match:
        return None

    hour = int(time_match.group(1))
    minute = int(time_match.group(2))
    # Use Bangkok time (UTC+7) for the base date so "Today"/"Tomorrow" resolve
    # correctly even when the scraper runs on a UTC server near midnight.
    _BKK = timezone(timedelta(hours=7))
    now = datetime.now(tz=_BKK).replace(tzinfo=None)

    lower = txt.lower()
    if "today" in lower:
        return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    elif "tomorrow" in lower:
        return (now + timedelta(days=1)).replace(
            hour=hour, minute=minute, second=0, microsecond=0
        )

    # Handle "D/M/YY at HH:MM" or "D/M/YYYY at HH:MM"
    date_match = re.match(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", txt)
    if date_match:
        day = int(date_match.group(1))
        month = int(date_match.group(2))
        year = int(date_match.group(3))
        if year < 100:
            year += 2000
        try:
            return datetime(year, month, day, hour, minute, 0)
        except ValueError:
            return None

    return None


def clean_currency(value_str: str | None) -> float:
    """Strip non-digit characters from a currency string and return a float.

    Handles common game formats like ``"1.000.000"`` (European dot separator),
    ``"$500,000"``, and plain numeric strings.

    Args:
        value_str: Currency string to parse. Pass ``None`` or an empty string
            to get ``0.0`` back.

    Returns:
        Numeric value as a :class:`float`, or ``0.0`` if the string is empty
        or contains no digits.

    Examples:
        >>> clean_currency("1,234,567")
        1234567.0
        >>> clean_currency("$500,000")
        500000.0
        >>> clean_currency(None)
        0.0
    """
    if not value_str:
        return 0.0
    clean = re.sub(r"[^\d]", "", str(value_str))
    return float(clean) if clean else 0.0
