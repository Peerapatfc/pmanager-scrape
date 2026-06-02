"""
Podcast pipeline entry script.

Detects completed matches not yet processed, scrapes their full match reports,
compiles source documents, generates dual-host podcast scripts via Claude API,
saves all files to output/podcasts/, and sends Telegram alerts.

Usage:
    python main_podcast_pipeline.py

Exit codes:
    0 — all pending matches processed (or none pending)
    1 — config validation failed
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.config import config
from src.core.logger import logger
from src.scrapers.match_report import MatchReportScraper
from src.services.podcast_compiler import PodcastCompiler
from src.services.podcast_generator import PodcastGenerator
from src.services.supabase_client import SupabaseManager
from src.services.telegram import TelegramBot

OUTPUT_ROOT = Path("output") / "podcasts"


def _safe_dirname(text: str) -> str:
    """Convert team name to a safe directory component."""
    return re.sub(r"[^\w\-]", "_", text).strip("_") or "Unknown"


def _output_dir(fixture: dict) -> Path:
    """Return the output directory for a given fixture."""
    date_part = (fixture.get("match_date") or "")[:10] or "unknown_date"
    competition = _safe_dirname(fixture.get("match_type") or "League")
    home = _safe_dirname(fixture.get("home_team_name") or "Home")
    away = _safe_dirname(fixture.get("away_team_name") or "Away")
    return OUTPUT_ROOT / date_part / competition / f"{home}_vs_{away}"


def _process_match(
    fixture: dict,
    scraper: MatchReportScraper,
    sm: SupabaseManager,
    generator: PodcastGenerator,
    bot: TelegramBot | None,
) -> bool:
    """Process one completed match through the full pipeline.

    Returns True on success, False on failure.
    """
    match_id = str(fixture["match_id"])
    home = fixture.get("home_team_name", "?")
    away = fixture.get("away_team_name", "?")
    result = fixture.get("result", "?")
    logger.info("Processing match %s: %s %s %s", match_id, home, result, away)

    # Step 1 — skip scrape if match_reports row already exists (resume partial run)
    existing = sm.get_match_report(match_id)
    screenshot_bytes: bytes | None = None
    if existing:
        logger.info("Match report already scraped for %s — skipping scrape", match_id)
        report = existing
    else:
        try:
            report = scraper.scrape(match_id, fixture)
            screenshot_bytes = report.pop("_screenshot_bytes", None)
            sm.upsert_match_report(report)
        except Exception as exc:
            logger.error("Scrape failed for match %s: %s", match_id, exc)
            _alert_failure(bot, f"Scrape failed for {home} vs {away} (match_id={match_id}): {exc}")
            return False

    # Step 2 — compile source document
    try:
        compiler = PodcastCompiler(match_id, sm)
        source_doc = compiler.compile()
    except Exception as exc:
        logger.error("Compile failed for match %s: %s", match_id, exc)
        _alert_failure(bot, f"Compile failed for {home} vs {away}: {exc}")
        return False

    # Step 3 — generate podcast script
    try:
        script = generator.generate(source_doc)
    except Exception as exc:
        logger.error("Script generation failed for match %s: %s", match_id, exc)
        _alert_failure(bot, f"Claude API failed for {home} vs {away}: {exc}")
        return False

    # Step 4 — write output files
    out_dir = _output_dir(fixture)
    out_dir.mkdir(parents=True, exist_ok=True)

    source_path = out_dir / "source_document.md"
    script_path = out_dir / "podcast_script.md"

    source_path.write_text(source_doc, encoding="utf-8")
    script_path.write_text(script, encoding="utf-8")
    if screenshot_bytes:
        (out_dir / "match_report.png").write_bytes(screenshot_bytes)
        logger.info("Saved match report screenshot to %s", out_dir / "match_report.png")
    logger.info("Saved output to %s", out_dir)

    # Step 5 — update DB (include full MD content for persistence)
    sm.update_match_report(
        match_id,
        podcast_path=str(out_dir),
        script_generated_at=datetime.now(tz=timezone.utc).isoformat(),
        source_doc=source_doc,
        podcast_script=script,
    )

    # Step 6 — Telegram alert
    msg = (
        f"Podcast script ready\n"
        f"{home} {result} {away}\n"
        f"Path: {out_dir}\n\n"
        f"Upload podcast_script.md to NotebookLM to generate audio."
    )
    if bot:
        try:
            bot.send_message(msg)
        except Exception as exc:
            logger.warning("Telegram alert failed: %s", exc)

    logger.info("Match %s processed successfully", match_id)
    return True


_CUP_KEYWORDS = ("cup", "taca", "taça", "copa", "national", "knockout")


def _alert_failure(bot: TelegramBot | None, msg: str) -> None:
    if bot:
        try:
            bot.send_message(f"Podcast pipeline error:\n{msg}")
        except Exception:
            pass


def _get_unprocessed_round_matches(
    pending: list[dict],
    sm: SupabaseManager,
) -> list[dict]:
    """Find other league round matches not yet scripted.

    Looks at league_matchday_results in recent match_reports to find match_ids
    for the other matches in each round (e.g. all 5 league matches per round).
    Matches already in match_reports with script_generated_at are skipped.

    Args:
        pending: Our team's pending matches (already queued for processing).
        sm:      SupabaseManager for DB queries.
    """
    # IDs already being handled as our own matches
    our_ids = {str(f["match_id"]) for f in pending}

    # Recent match_reports that contain round data (league_matchday_results).
    # Sort so pending matches come first — they were just scraped and have the
    # correct round's calendar data. Non-pending parents scraped previously may
    # contain stale global calendar data (always shows most-recent completed round),
    # so their round match IDs are wrong. `seen` dedup ensures the pending parent
    # wins by being processed first.
    pending_ids = {str(f["match_id"]) for f in pending}
    recent_raw = sm.get_recent_league_match_reports(lookback_days=7)
    recent = sorted(recent_raw, key=lambda r: str(r.get("match_id", "")) not in pending_ids)

    # IDs already scripted — skip these
    seen: set[str] = set(our_ids)
    results: list[dict] = []

    for parent in recent:
        league_results = parent.get("league_matchday_results") or []

        # Use actual match_date and match_type from upcoming_fixtures
        parent_fixture = sm.get_fixture_by_match_id(str(parent.get("match_id", "")))
        match_date = (
            (parent_fixture or {}).get("match_date")
            or (parent.get("scraped_at") or "")[:10]
        )
        match_type = (parent_fixture or {}).get("match_type") or "League"

        for r in league_results:
            mid = str(r.get("match_id") or "")
            if not mid or mid in seen:
                continue
            seen.add(mid)

            existing = sm.get_match_report(mid)
            if existing and existing.get("script_generated_at"):
                continue

            results.append({
                "match_id":       mid,
                "home_team_name": r.get("home_team", "Home"),
                "away_team_name": r.get("away_team", "Away"),
                "result":         r.get("result", "?-?"),
                "match_type":     match_type,
                "match_date":     match_date,
                "season":         config.CURRENT_SEASON,
                "_round_results": league_results,
            })

    return results


def _process_round_match(
    fixture: dict,
    scraper: MatchReportScraper,
    sm: SupabaseManager,
    generator: PodcastGenerator,
    bot: TelegramBot | None,
) -> bool:
    """Process one round match (another team's match in the same league round).

    Uses fixture_override in the compiler (no upcoming_fixtures row, no scouting
    data) and reuses pre-scraped round results to avoid duplicate requests.
    """
    match_id = str(fixture["match_id"])
    home = fixture.get("home_team_name", "?")
    away = fixture.get("away_team_name", "?")
    result = fixture.get("result", "?")
    logger.info("Processing round match %s: %s %s %s", match_id, home, result, away)

    existing = sm.get_match_report(match_id)
    screenshot_bytes: bytes | None = None
    if existing:
        logger.info("Round match report already scraped for %s — skipping scrape", match_id)
    else:
        try:
            report = scraper.scrape(match_id, fixture)
            screenshot_bytes = report.pop("_screenshot_bytes", None)
            # Reuse pre-scraped round results to avoid re-scraping the calendar
            report["league_matchday_results"] = fixture.get("_round_results", [])
            sm.upsert_match_report(report)
        except Exception as exc:
            logger.error("Scrape failed for round match %s: %s", match_id, exc)
            _alert_failure(bot, f"Scrape failed for {home} vs {away} (round match): {exc}")
            return False

    try:
        compiler = PodcastCompiler(match_id, sm)
        source_doc = compiler.compile(fixture_override=fixture)
    except Exception as exc:
        logger.error("Compile failed for round match %s: %s", match_id, exc)
        _alert_failure(bot, f"Compile failed for {home} vs {away} (round match): {exc}")
        return False

    try:
        script = generator.generate(source_doc)
    except Exception as exc:
        logger.error("Script generation failed for round match %s: %s", match_id, exc)
        _alert_failure(bot, f"Gemini API failed for {home} vs {away} (round match): {exc}")
        return False

    out_dir = _output_dir(fixture)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "source_document.md").write_text(source_doc, encoding="utf-8")
    (out_dir / "podcast_script.md").write_text(script, encoding="utf-8")
    if screenshot_bytes:
        (out_dir / "match_report.png").write_bytes(screenshot_bytes)
        logger.info("Saved match report screenshot to %s", out_dir / "match_report.png")
    logger.info("Saved round match output to %s", out_dir)

    sm.update_match_report(
        match_id,
        podcast_path=str(out_dir),
        script_generated_at=datetime.now(tz=timezone.utc).isoformat(),
        source_doc=source_doc,
        podcast_script=script,
    )

    if bot:
        try:
            bot.send_message(
                f"Podcast script ready (round match)\n"
                f"{home} {result} {away}\n"
                f"Path: {out_dir}",
                markdown=False,
            )
        except Exception as exc:
            logger.warning("Telegram alert failed: %s", exc)

    logger.info("Round match %s processed successfully", match_id)
    return True


def main() -> None:
    config.validate_podcast()

    sm  = SupabaseManager()
    gen = PodcastGenerator()
    bot: TelegramBot | None = None
    if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
        bot = TelegramBot()

    pending = sm.get_pending_match_reports()
    round_matches = _get_unprocessed_round_matches(pending, sm)

    total = len(pending) + len(round_matches)
    if not total:
        logger.info("No pending matches to process.")
        return

    logger.info(
        "Processing %d our match(es) + %d round match(es)...",
        len(pending), len(round_matches),
    )
    success_count = 0
    fail_count    = 0

    with MatchReportScraper() as scraper:
        scraper.login(config.PM_USERNAME, config.PM_PASSWORD)

        for fixture in pending:
            ok = _process_match(fixture, scraper, sm, gen, bot)
            if ok:
                success_count += 1
            else:
                fail_count += 1

        # Re-collect round matches now that our matches are processed and their
        # league_matchday_results (with match_ids) are stored in match_reports
        round_matches = _get_unprocessed_round_matches(pending, sm)
        if round_matches:
            logger.info("Processing %d other round match(es)...", len(round_matches))
            for fixture in round_matches:
                ok = _process_round_match(fixture, scraper, sm, gen, bot)
                if ok:
                    success_count += 1
                else:
                    fail_count += 1

    logger.info(
        "Pipeline complete. Success: %d, Failed: %d",
        success_count, fail_count,
    )
    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
