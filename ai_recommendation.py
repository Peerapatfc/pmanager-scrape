"""
AI recommendation alert entry point.

Reads the current transfer market from Supabase, applies profit/budget/timing
filters, and prints the top opportunities.

Filter criteria (constants in :mod:`src.constants`):
- Asking price ≤ :data:`~src.constants.MAX_BUDGET` AND ≤ available team funds
- Forecast profit > 0
- Auction deadline within :data:`~src.constants.ALERT_HORIZON_HOURS` hours
- Top :data:`~src.constants.TOP_ALERTS_LIMIT` results sorted by forecast profit

Usage::

    python ai_recommendation.py
"""

from datetime import datetime, timedelta
from typing import Any

from src import constants
from src.config import config
from src.core.logger import logger
from src.core.utils import clean_currency, parse_deadline
from src.services.supabase_client import SupabaseManager


def _filter_candidates(
    transfer_data: list[dict[str, Any]],
    current_funds: float,
    now_th: datetime,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Apply budget, profit, and timing filters to transfer listings.

    Args:
        transfer_data: All rows from the ``transfer_listings`` table.
        current_funds: Available team funds (game currency).
        now_th: Current local time (UTC+7) used to evaluate deadlines.

    Returns:
        Tuple of ``(candidates, dropped_stats)`` where ``candidates`` is the
        filtered list (with ``net_profit`` and formatted ``deadline`` injected)
        and ``dropped_stats`` is a dict counting rows dropped per reason.
    """
    candidates: list[dict[str, Any]] = []
    dropped: dict[str, int] = {"budget": 0, "profit": 0, "time": 0, "parse_error": 0}
    horizon_seconds = constants.ALERT_HORIZON_HOURS * 3600

    for p in transfer_data:
        try:
            buy_price = int(p.get("asking_price", 0))

            if buy_price > current_funds or buy_price > constants.MAX_BUDGET:
                dropped["budget"] += 1
                continue

            net_profit = 0
            fp_raw = p.get("forecast_profit", "")
            if fp_raw and str(fp_raw).strip():
                net_profit = int(float(fp_raw))

            p["net_profit"] = net_profit

            if net_profit <= 0:
                dropped["profit"] += 1
                continue

            deadline_str = str(p.get("deadline", ""))
            deadline_dt = None
            if deadline_str and deadline_str not in ("None", "N/A"):
                try:
                    # DB stores deadlines as ISO strings (e.g. "2026-04-10T09:25:00+00:00").
                    # Strip timezone info and treat as naive Bangkok time — consistent with
                    # how parse_deadline() and now_th are both computed in UTC+7.
                    deadline_dt = datetime.fromisoformat(deadline_str).replace(tzinfo=None)
                except ValueError:
                    deadline_dt = parse_deadline(deadline_str)

            if not deadline_dt:
                dropped["parse_error"] += 1
                continue

            diff_seconds = (deadline_dt - now_th).total_seconds()
            if 0 < diff_seconds < horizon_seconds:
                p["deadline"] = deadline_dt.strftime("%d/%m %H:%M")
                candidates.append(p)
            else:
                dropped["time"] += 1

        except Exception as e:
            logger.debug("Skipping row during filtering: %s", e)

    return candidates, dropped


def generate_message(
    candidates: list[dict[str, Any]],
    funds_str: str,
    current_time_th: datetime,
) -> str:
    """Build the Telegram alert message from the filtered candidate list.

    Args:
        candidates: Filtered and sorted list of transfer opportunities.
        funds_str: Human-readable available funds string (for display).
        current_time_th: Current local time (UTC+7) for the timestamp header.

    Returns:
        Formatted Telegram Markdown message string.
    """
    time_str = current_time_th.strftime("%H:%M ICT")

    if not candidates:
        return (
            f"📉 *Market Update* ({time_str})\n\n"
            "No profitable flips found within budget right now."
        )

    msg = f"🚀 *Top {constants.TOP_ALERTS_LIMIT} Day Trade Signals (Algorithm)* 🚀\n\n"
    msg += f"💰 Budget: {funds_str}\n"
    msg += f"⏰ Time: {time_str}\n\n"

    for i, p in enumerate(candidates[: constants.TOP_ALERTS_LIMIT], 1):
        name = p.get("name", "N/A")
        pid = p.get("id", "")
        buy = f"{int(p.get('asking_price', 0)):,}"
        profit_val = p.get("net_profit", 0)
        profit_str = f"{int(profit_val):,}"
        deadline = p.get("deadline", "N/A")
        profit_icon = "🤑" if profit_val > 10_000_000 else "💵"

        msg += (
            f"{i}. *{name}*\n"
            f"   📉 Buy: {buy} | {profit_icon} Profit: {profit_str}\n"
            f"   ⏱️ Ends: {deadline}\n"
            f"   🔗 Link: https://www.pmanager.org/comprar_jog_lista.asp?jg_id={pid}\n\n"
        )

    msg += "⚠️ *Auto-generated based on (Est. Value/2 * 0.8) - Buy Price*"
    return msg


def main() -> None:
    """Fetch transfer data, filter top opportunities, and print results."""
    config.validate()

    now_th = datetime.utcnow() + timedelta(hours=constants.UTC_OFFSET_HOURS)

    db = SupabaseManager()

    transfer_data = db.get_all_transfer_listings()
    if not transfer_data:
        logger.warning("No transfer data found.")
        return

    # Get team funds for budget filter
    team_info = db.get_team_info()
    current_funds = 0.0
    funds_str = "0"
    if team_info:
        funds_raw = team_info.get("available_funds", "0")
        funds_str = str(funds_raw)
        current_funds = clean_currency(funds_raw)

    logger.info("Current Funds: %s", f"{current_funds:,.0f}")
    logger.info("Current Time (TH): %s", now_th)

    candidates, dropped = _filter_candidates(transfer_data, current_funds, now_th)
    candidates.sort(key=lambda x: int(x.get("net_profit", 0)), reverse=True)

    logger.info(
        "Filter Summary: Passed=%d, Dropped=%s", len(candidates), dropped
    )

    msg = generate_message(candidates, funds_str, now_th)
    logger.info("\n%s", msg)


if __name__ == "__main__":
    main()
