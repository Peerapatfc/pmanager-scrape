"""
Import a manually assembled round source document into league_match_results.

Reads a Markdown source document (produced by RoundCompiler or assembled
manually), parses structured match data, and upserts into Supabase.

Usage:
    python main_import_round.py <path_to_source_doc.md>
    python main_import_round.py --stdin          # read from stdin

Exit codes:
    0 — success
    1 — parse error or Supabase failure
"""

from __future__ import annotations

import sys
from pathlib import Path

from src.config import config
from src.core.logger import logger
from src.services.match_doc_parser import parse_source_doc
from src.services.supabase_client import SupabaseManager


def main() -> None:
    config.validate()

    # --- Read input ---
    args = sys.argv[1:]
    if not args:
        print("Usage: python main_import_round.py <source_doc.md>  |  --stdin")
        sys.exit(1)

    if args[0] == "--stdin":
        text = sys.stdin.read()
        source = "stdin"
    else:
        path = Path(args[0])
        if not path.exists():
            logger.error("File not found: %s", path)
            sys.exit(1)
        text = path.read_text(encoding="utf-8")
        source = str(path)

    logger.info("Parsing source document from %s (%d chars)", source, len(text))

    # --- Parse ---
    try:
        doc = parse_source_doc(text)
    except ValueError as exc:
        logger.error("Parse failed: %s", exc)
        sys.exit(1)

    competition = doc["competition"]
    date        = doc["date"]
    round_key   = doc["round_key"]
    matches     = doc["matches"]

    logger.info(
        "Parsed: competition=%s  date=%s  round_key=%s  matches=%d",
        competition, date, round_key, len(matches),
    )

    if not matches:
        logger.warning("No matches found in source document — nothing to import.")
        sys.exit(0)

    # Log parse summary
    for m in matches:
        gid   = m.get("game_id") or "NO_ID"
        home  = m.get("home_team", "?")
        away  = m.get("away_team", "?")
        hs    = m.get("home_score", "?")
        as_   = m.get("away_score", "?")
        at_ok = "OK" if m.get("home_at") else "MISSING"
        st_ok = "OK" if m.get("stats") else "MISSING"
        logger.info("  [%s] %s %s-%s %s  AT:%s  Stats:%s", gid, home, hs, as_, away, at_ok, st_ok)

    # Check for matches without game_id — those will be skipped in upsert
    no_id = [m for m in matches if not m.get("game_id")]
    if no_id:
        logger.warning(
            "%d match(es) have no game_id and will be skipped: %s",
            len(no_id),
            [f"{m['home_team']} vs {m['away_team']}" for m in no_id],
        )

    # --- Upsert ---
    sm = SupabaseManager()
    sm.upsert_league_match_results(matches)

    imported = len([m for m in matches if m.get("game_id")])
    logger.info("Done. Imported %d/%d matches for round %s.", imported, len(matches), round_key)


if __name__ == "__main__":
    main()
