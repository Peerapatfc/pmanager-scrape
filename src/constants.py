"""
Project-wide constants for pmanager-scrape.

All magic numbers, thresholds, and configuration values should be defined here
rather than scattered through business logic. Import from this module instead
of duplicating literals.
"""

# ---------------------------------------------------------------------------
# Timezone
# ---------------------------------------------------------------------------

UTC_OFFSET_HOURS: int = 7
"""UTC offset for the local game server timezone (UTC+7)."""

# ---------------------------------------------------------------------------
# Business logic thresholds
# ---------------------------------------------------------------------------

MAX_BUDGET: int = 30_000_000
"""Maximum asking price (in game currency) to include in Telegram alerts."""

ALERT_HORIZON_HOURS: int = 12
"""Only alert on listings whose auction deadline is within this many hours."""

TOP_ALERTS_LIMIT: int = 15
"""Maximum number of opportunities to include in a single Telegram alert."""

FINAL_PRICE_GRACE_HOURS: int = 2
"""Skip updating a player's final price if it was updated within this window."""

# ---------------------------------------------------------------------------
# Scraper / database settings
# ---------------------------------------------------------------------------

DEFAULT_BATCH_SIZE: int = 500
"""Maximum rows per Supabase upsert batch (free-tier safe limit)."""

BOT_EVAL_BATCH_SIZE: int = 2_200
"""Number of bot players to evaluate in a single run of main_bot_evaluate.py."""

MAX_DIVISION: int = 2
"""Only scrape the top N divisions per country during BOT team discovery."""

# ---------------------------------------------------------------------------
# BOT player quality filter
# ---------------------------------------------------------------------------

BOT_ACCEPTED_QUALITIES: tuple[str, ...] = ("World Class", "Formidable", "Excellent")
"""Quality tiers that qualify a BOT player for the opportunities table."""

# ---------------------------------------------------------------------------
# Business formula coefficients
# ---------------------------------------------------------------------------

FORECAST_SELL_DIVISOR: float = 2.0
"""Divisor applied to estimated value in the conservative resale forecast."""

FORECAST_SELL_MULTIPLIER: float = 0.8
"""Multiplier applied after dividing to account for market discount."""
# forecast_sell = (estimated_value / FORECAST_SELL_DIVISOR) * FORECAST_SELL_MULTIPLIER

# ---------------------------------------------------------------------------
# Frontend / UI (used by Next.js via separate constants.ts — kept here for
# documentation parity only)
# ---------------------------------------------------------------------------

DEFAULT_PAGE_SIZE: int = 50
"""Default number of rows per page in dashboard tables."""

DEBOUNCE_MS: int = 500
"""Debounce delay (milliseconds) for search input in the dashboard."""
