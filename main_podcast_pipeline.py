"""
Podcast pipeline entry script.

Phase 1 — Scrape: detect completed matches, scrape full match reports,
save screenshots per match, upsert to match_reports.

Phase 2 — Compile & Generate: group scraped matches by round, compile one
combined source document per round via RoundCompiler, generate one podcast
script per round via Gemini API, save files, upsert to round_reports, alert.

Usage:
    python main_podcast_pipeline.py

Exit codes:
    0 — all pending rounds processed (or none pending)
    1 — config validation failed or at least one round failed
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.config import config
from src.core.logger import logger
from src.scrapers.league_stats import LeagueStatsScraper
from src.scrapers.match_report import MatchReportScraper
from src.services.podcast_compiler import RoundCompiler
from src.services.podcast_generator import PodcastGenerator
from src.services.supabase_client import SupabaseManager
from src.services.telegram import TelegramBot

OUTPUT_ROOT = Path("output") / "podcasts"


def _safe_dirname(text: str) -> str:
    return re.sub(r"[^\w\-]", "_", text).strip("_") or "Unknown"


def _round_key(date: str, match_type: str) -> str:
    return f"{date[:10]}___{_safe_dirname(match_type)}"


def _round_output_dir(date: str, match_type: str) -> Path:
    return OUTPUT_ROOT / date[:10] / _safe_dirname(match_type)


def _match_output_dir(fixture: dict) -> Path:
    date  = (fixture.get("match_date") or "")[:10] or "unknown_date"
    mtype = _safe_dirname(fixture.get("match_type") or "League")
    home  = _safe_dirname(fixture.get("home_team_name") or "Home")
    away  = _safe_dirname(fixture.get("away_team_name") or "Away")
    return OUTPUT_ROOT / date / mtype / f"{home}_vs_{away}"


def _alert_failure(bot: TelegramBot | None, msg: str) -> None:
    if bot:
        try:
            bot.send_message(f"Podcast pipeline error:\n{msg}")
        except Exception:
            pass


# ------------------------------------------------------------------ #
# Phase 1 — scrape helpers                                            #
# ------------------------------------------------------------------ #

def _scrape_match(
    fixture: dict,
    scraper: MatchReportScraper,
    sm: SupabaseManager,
    bot: TelegramBot | None,
) -> bool:
    """Scrape one match report and save screenshot. Returns True on success."""
    match_id = str(fixture["match_id"])
    home = fixture.get("home_team_name", "?")
    away = fixture.get("away_team_name", "?")

    existing = sm.get_match_report(match_id)
    if existing:
        logger.info("Match report already scraped for %s — skipping", match_id)
        return True

    try:
        report = scraper.scrape(match_id, fixture)
        screenshot_bytes: bytes | None = report.pop("_screenshot_bytes", None)
        sm.upsert_match_report(report)

        if screenshot_bytes:
            out_dir = _match_output_dir(fixture)
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "match_report.png").write_bytes(screenshot_bytes)
            logger.info("Saved screenshot: %s", out_dir / "match_report.png")

        return True
    except Exception as exc:
        logger.error("Scrape failed for match %s: %s", match_id, exc)
        _alert_failure(bot, f"Scrape failed for {home} vs {away} (match_id={match_id}): {exc}")
        return False


# ------------------------------------------------------------------ #
# Round detection helpers                                              #
# ------------------------------------------------------------------ #

_CUP_KEYWORDS = ("cup", "taca", "taça", "copa", "national", "knockout")


def _get_unprocessed_round_matches(
    pending: list[dict],
    sm: SupabaseManager,
) -> list[dict]:
    """Return synthetic fixture dicts for other-team round matches not yet scraped."""
    our_ids     = {str(f["match_id"]) for f in pending}
    pending_ids = our_ids

    # Seed seen with every match_id already committed to a completed round so that
    # stale league_matchday_results (game page caching previous round data) cannot
    # assign old match_ids to the new round.
    seen: set[str] = set(our_ids)
    for done in sm.get_all_round_reports():
        for s in (done.get("match_summaries") or []):
            mid = str(s.get("match_id") or "")
            if mid:
                seen.add(mid)

    recent_raw = sm.get_recent_league_match_reports(lookback_days=7)
    recent     = sorted(recent_raw, key=lambda r: str(r.get("match_id", "")) not in pending_ids)

    results: list[dict] = []

    for parent in recent:
        league_results = parent.get("league_matchday_results") or []
        parent_fixture = sm.get_fixture_by_match_id(str(parent.get("match_id", "")))
        match_date     = (parent_fixture or {}).get("match_date") or (parent.get("scraped_at") or "")[:10]
        match_type     = (parent_fixture or {}).get("match_type") or "League"

        for r in league_results:
            mid = str(r.get("match_id") or "")
            if not mid or mid in seen:
                continue
            seen.add(mid)

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


def _scrape_round_match(
    fixture: dict,
    scraper: MatchReportScraper,
    sm: SupabaseManager,
    bot: TelegramBot | None,
) -> bool:
    """Scrape a round match (other team). Returns True on success."""
    match_id = str(fixture["match_id"])
    home     = fixture.get("home_team_name", "?")
    away     = fixture.get("away_team_name", "?")

    existing = sm.get_match_report(match_id)
    if existing:
        logger.info("Round match already scraped for %s — skipping", match_id)
        return True

    try:
        report = scraper.scrape(match_id, fixture)
        screenshot_bytes: bytes | None = report.pop("_screenshot_bytes", None)
        report["league_matchday_results"] = fixture.get("_round_results", [])
        sm.upsert_match_report(report)

        if screenshot_bytes:
            out_dir = _match_output_dir(fixture)
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "match_report.png").write_bytes(screenshot_bytes)
            logger.info("Saved screenshot: %s", out_dir / "match_report.png")

        return True
    except Exception as exc:
        logger.error("Scrape failed for round match %s: %s", match_id, exc)
        _alert_failure(bot, f"Scrape failed for {home} vs {away} (round match): {exc}")
        return False


# ------------------------------------------------------------------ #
# Phase 2 — round grouping + generation                               #
# ------------------------------------------------------------------ #

def _group_into_rounds(fixtures: list[dict]) -> list[dict]:
    """Group fixture dicts by (date, match_type) into round_meta dicts."""
    from collections import defaultdict
    groups: dict[str, list[dict]] = defaultdict(list)

    for f in fixtures:
        date  = (f.get("match_date") or "")[:10] or "unknown"
        mtype = f.get("match_type") or "League"
        key   = _round_key(date, mtype)
        groups[key].append(f)

    rounds = []
    for key, fixs in groups.items():
        f0    = fixs[0]
        date  = (f0.get("match_date") or "")[:10]
        mtype = f0.get("match_type") or "League"
        rounds.append({
            "round_key":   key,
            "date":        date,
            "competition": mtype,
            "match_summaries": [
                {
                    "match_id": str(f["match_id"]),
                    "home":     f.get("home_team_name", "?"),
                    "away":     f.get("away_team_name", "?"),
                    "result":   f.get("result", "?"),
                }
                for f in fixs
            ],
        })

    return rounds


def _process_round(
    round_meta: dict,
    sm: SupabaseManager,
    compiler: RoundCompiler,
    generator: PodcastGenerator,
    bot: TelegramBot | None,
    source_only: bool = False,
    league_stats: dict | None = None,
) -> bool:
    """Compile + (optionally) generate + save one round. Returns True on success."""
    rkey        = round_meta["round_key"]
    competition = round_meta["competition"]
    date        = round_meta["date"]
    summaries   = round_meta["match_summaries"]

    logger.info("Processing round %s (%d matches)", rkey, len(summaries))

    # Skip if round already scripted (unless source_only — allow re-compiling source doc)
    existing = sm.get_round_report(rkey)
    if not source_only and existing and existing.get("generated_at"):
        logger.info("Round %s already scripted — skipping", rkey)
        return True

    # Compile
    try:
        source_doc = compiler.compile(round_meta, league_stats=league_stats)
    except Exception as exc:
        logger.error("Compile failed for round %s: %s", rkey, exc)
        _alert_failure(bot, f"Compile failed for {competition} {date}: {exc}")
        return False

    # Save files to round folder
    out_dir = _round_output_dir(date, competition)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "source_document.md").write_text(source_doc, encoding="utf-8")
    logger.info("Saved source document to %s", out_dir)

    if source_only:
        # Upsert source_doc only — leave podcast_script untouched
        sm.upsert_round_report({
            "round_key":       rkey,
            "date":            date,
            "competition":     competition,
            "match_summaries": summaries,
            "source_doc":      source_doc,
        })
        logger.info("Round %s source doc saved (script generation skipped)", rkey)
        return True

    # Generate podcast script via Gemini
    try:
        script = generator.generate(source_doc)
    except Exception as exc:
        logger.error("Script generation failed for round %s: %s", rkey, exc)
        _alert_failure(bot, f"Gemini API failed for {competition} {date}: {exc}")
        return False

    (out_dir / "podcast_script.md").write_text(script, encoding="utf-8")

    sm.upsert_round_report({
        "round_key":       rkey,
        "date":            date,
        "competition":     competition,
        "match_summaries": summaries,
        "source_doc":      source_doc,
        "podcast_script":  script,
        "generated_at":    datetime.now(tz=timezone.utc).isoformat(),
    })

    for s in summaries:
        sm.update_match_report(
            str(s["match_id"]),
            script_generated_at=datetime.now(tz=timezone.utc).isoformat(),
        )

    if bot:
        results_txt = "\n".join(
            f"  {s['home']} {s['result']} {s['away']}" for s in summaries
        )
        bot.send_message(
            f"Podcast script ready\n"
            f"{competition} — {date}\n"
            f"{results_txt}\n\n"
            f"Path: {out_dir}",
            markdown=False,
        )

    logger.info("Round %s processed successfully", rkey)
    return True


# ------------------------------------------------------------------ #
# Main                                                                 #
# ------------------------------------------------------------------ #

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Podcast pipeline")
    parser.add_argument(
        "--source-only",
        action="store_true",
        help="Compile source documents only — skip Gemini script generation",
    )
    args = parser.parse_args()

    config.validate_podcast()

    sm       = SupabaseManager()
    gen      = PodcastGenerator()
    compiler = RoundCompiler(sm)
    bot: TelegramBot | None = None
    if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
        bot = TelegramBot()

    pending = sm.get_pending_match_reports()
    if not pending:
        logger.info("No pending matches to process.")
        return

    logger.info("Found %d pending match(es) to scrape.", len(pending))

    # ---- Phase 1: scrape all matches + league stats -----------------
    scraped_fixtures: list[dict] = []
    failed_scrape = 0
    league_stats: dict | None = None

    with MatchReportScraper() as scraper:
        scraper.login(config.PM_USERNAME, config.PM_PASSWORD)

        for fixture in pending:
            ok = _scrape_match(fixture, scraper, sm, bot)
            if ok:
                scraped_fixtures.append(fixture)
            else:
                failed_scrape += 1

        # Discover other round matches now that our reports are in DB
        round_matches = _get_unprocessed_round_matches(pending, sm)
        logger.info("Discovered %d other round match(es).", len(round_matches))

        for fixture in round_matches:
            ok = _scrape_round_match(fixture, scraper, sm, bot)
            if ok:
                scraped_fixtures.append(fixture)
            else:
                failed_scrape += 1

        # Scrape league-wide stats for source document enrichment
        try:
            stats_scraper = LeagueStatsScraper()
            stats_scraper.page = scraper.page  # reuse authenticated browser page
            league_stats = stats_scraper.scrape_all()
            logger.info("League stats scraped successfully.")
        except Exception as exc:
            logger.warning("League stats scrape failed (non-fatal): %s", exc)
            league_stats = None

    if not scraped_fixtures:
        logger.error("No matches scraped successfully.")
        sys.exit(1)

    # ---- Phase 2: group into rounds + generate ----------------------
    rounds = _group_into_rounds(scraped_fixtures)
    logger.info("Generating scripts for %d round(s)...", len(rounds))

    success_count = 0
    fail_count    = failed_scrape

    for round_meta in rounds:
        ok = _process_round(round_meta, sm, compiler, gen, bot, source_only=args.source_only, league_stats=league_stats)
        if ok:
            success_count += 1
        else:
            fail_count += 1

    logger.info(
        "Pipeline complete. Rounds: %d success, %d failed.",
        success_count, fail_count,
    )
    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
