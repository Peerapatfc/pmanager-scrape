"""
Supabase database client for pmanager-scrape.

Provides :class:`SupabaseManager` which wraps all database operations
(upserts, reads, deletes) for the four project tables: ``players``,
``transfer_listings``, ``bot_opportunities``, and ``team_info``.

All write methods coerce NumPy / Pandas types to native Python before
sending to Supabase, since the client library rejects ``np.int64`` etc.
"""

from __future__ import annotations

from typing import Any

from supabase import create_client

from src import constants
from src.config import config
from src.core.logger import logger


class SupabaseManager:
    """High-level interface for all Supabase database operations."""

    def __init__(self) -> None:
        self.client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_native(val: Any) -> Any:
        """Convert NumPy / Pandas scalar types to native Python equivalents.

        The Supabase Python client serialises values with ``json.dumps`` which
        cannot handle ``np.int64``, ``np.float64``, etc. This helper converts
        any such value to its native Python counterpart.

        Args:
            val: Any value, potentially a NumPy scalar.

        Returns:
            A JSON-serialisable native Python value.
        """
        try:
            import numpy as np  # optional dependency — only used if pandas is installed

            if isinstance(val, np.ndarray):
                return val.tolist()
            if isinstance(val, np.integer):
                return int(val)
            if isinstance(val, np.floating):
                v = float(val)
                return 0 if (np.isnan(v) or np.isinf(v)) else v
            if isinstance(val, np.bool_):
                return bool(val)
        except ImportError:
            pass

        return val

    def _coerce_record(
        self,
        row: dict[str, Any],
        int_cols: tuple[str, ...] = (),
        float_cols: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        """Apply standard type coercions to a database row dict.

        Converts integer columns from string/float to ``int`` and float
        columns from string to ``float``, handling empty strings and
        ``ValueError`` / ``TypeError`` gracefully.

        Args:
            row: Mutable dict of column → value pairs (modified in place).
            int_cols: Column names that should be coerced to ``int``.
            float_cols: Column names that should be coerced to ``float``.

        Returns:
            The same ``row`` dict after coercions have been applied.
        """
        if "age" in row:
            try:
                row["age"] = int(row["age"]) if row["age"] else None
            except (ValueError, TypeError):
                row["age"] = None

        for col in int_cols:
            if col in row:
                try:
                    row[col] = int(row[col]) if row[col] != "" else 0
                except (ValueError, TypeError):
                    row[col] = 0

        for col in float_cols:
            if col in row:
                try:
                    row[col] = float(row[col]) if row[col] != "" else 0.0
                except (ValueError, TypeError):
                    row[col] = 0.0

        return row

    def _upsert_batched(self, table: str, rows: list[dict[str, Any]]) -> None:
        """Upsert rows into a Supabase table in safe batch sizes.

        Args:
            table: Target table name.
            rows: List of row dicts to upsert.
        """
        batch_size = constants.DEFAULT_BATCH_SIZE
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            try:
                self.client.table(table).upsert(batch).execute()
            except Exception as e:
                logger.error(
                    "Failed to upsert %s batch starting at row %d: %s", table, i, e
                )

    # ------------------------------------------------------------------
    # players table
    # ------------------------------------------------------------------

    def upsert_players(self, records: list[dict[str, Any]]) -> None:
        """Batch upsert player records into the ``players`` table.

        Known schema columns are mapped to their DB column names; all other
        keys are packed into the ``skills`` JSONB column.

        Args:
            records: List of raw player dicts from the scraper.
        """
        KNOWN_COLS = {
            "id", "name", "position", "age", "nationality",
            "Quality", "Potential", "Affected Quality",
            "bids_count", "bids_avg", "deadline", "url",
            "last_transfer_price", "sale_to_bid_ratio",
        }
        KNOWN_DB_COLS = {
            "id", "name", "position", "age", "nationality",
            "quality", "potential", "affected_quality",
            "bids_count", "bids_avg", "deadline", "url",
            "last_transfer_price", "sale_to_bid_ratio",
        }

        rows: list[dict[str, Any]] = []
        for rec in records:
            row: dict[str, Any] = {}
            skills: dict[str, Any] = {}

            for key, val in rec.items():
                db_key = key.lower().replace(" ", "_")
                if key in KNOWN_COLS or db_key in KNOWN_DB_COLS:
                    row[db_key] = self._to_native(val)
                else:
                    skills[key] = self._to_native(val)

            row["skills"] = skills

            if "id" not in row or not row["id"]:
                continue

            row["id"] = str(row["id"])
            self._coerce_record(row)
            rows.append(row)

        if not rows:
            return

        self._upsert_batched("players", rows)
        logger.info("Upserted %d rows to 'players'", len(rows))

    def get_all_players(self) -> list[dict[str, Any]]:
        """Fetch all player records from the ``players`` table.

        Returns:
            List of player row dicts, or an empty list on error.
        """
        try:
            resp = self.client.table("players").select("*").execute()
            return resp.data or []
        except Exception as e:
            logger.error("Failed to fetch players: %s", e)
            return []

    def update_player(self, player_id: str, data: dict[str, Any]) -> None:
        """Update specific fields on a single player row.

        Args:
            player_id: Supabase row ID of the player.
            data: Dict of column → new value pairs.
        """
        clean = {k: self._to_native(v) for k, v in data.items()}
        try:
            self.client.table("players").update(clean).eq("id", str(player_id)).execute()
        except Exception as e:
            logger.error("Failed to update player %s: %s", player_id, e)

    # ------------------------------------------------------------------
    # transfer_listings table
    # ------------------------------------------------------------------

    def replace_transfer_listings(self, records: list[dict[str, Any]]) -> None:
        """Full-replace the ``transfer_listings`` table with new data.

        Deletes all existing rows, then inserts the provided records in batches.

        Args:
            records: List of transfer listing dicts from the scraper.
        """
        COL_MAP = {
            "id": "id",
            "name": "name",
            "position": "position",
            "age": "age",
            "Quality": "quality",
            "Potential": "potential",
            "estimated_value": "estimated_value",
            "asking_price": "asking_price",
            "value_diff": "value_diff",
            "roi": "roi",
            "forecast_sell": "forecast_sell",
            "forecast_profit": "forecast_profit",
            "deadline": "deadline",
            "url": "url",
            "last_updated": "last_updated",
        }

        rows: list[dict[str, Any]] = []
        for rec in records:
            row: dict[str, Any] = {}
            for src_key, db_key in COL_MAP.items():
                if src_key in rec:
                    row[db_key] = self._to_native(rec[src_key])

            if "id" not in row or not row["id"]:
                continue
            row["id"] = str(row["id"])

            self._coerce_record(
                row,
                int_cols=("estimated_value", "asking_price", "value_diff"),
                float_cols=("roi", "forecast_sell", "forecast_profit"),
            )
            rows.append(row)

        if not rows:
            return

        try:
            # Delete all existing rows for a full replace.
            # neq("id", "0") is a filter that matches every real row since
            # no player ID will ever be the string "0".
            logger.info("Clearing existing transfer listings...")
            self.client.table("transfer_listings").delete().neq("id", "0").execute()
        except Exception as e:
            logger.error("Failed to clear old transfer_listings: %s", e)

        batch_size = constants.DEFAULT_BATCH_SIZE
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            try:
                self.client.table("transfer_listings").insert(batch).execute()
            except Exception as e:
                logger.error(
                    "Failed to insert transfer_listings batch starting at row %d: %s", i, e
                )

        logger.info("Replaced %d rows in 'transfer_listings'", len(rows))

    def get_all_transfer_listings(self) -> list[dict[str, Any]]:
        """Fetch all transfer listing records.

        Returns:
            List of transfer listing row dicts, or an empty list on error.
        """
        try:
            resp = self.client.table("transfer_listings").select("*").execute()
            return resp.data or []
        except Exception as e:
            logger.error("Failed to fetch transfer_listings: %s", e)
            return []

    # ------------------------------------------------------------------
    # bot_opportunities table
    # ------------------------------------------------------------------

    def upsert_bot_opportunities(self, records: list[dict[str, Any]]) -> None:
        """Batch upsert BOT opportunity records.

        Args:
            records: List of opportunity dicts from the scraper.
        """
        COL_MAP = {
            "id": "id",
            "name": "name",
            "position": "position",
            "age": "age",
            "quality": "quality",
            "team_name": "team_name",
            "estimated_value": "estimated_value",
            "asking_price": "asking_price",
            "value_diff": "value_diff",
            "profit_margin": "profit_margin",
            "url": "url",
            "last_evaluated_at": "last_evaluated_at",
        }

        rows: list[dict[str, Any]] = []
        for rec in records:
            row: dict[str, Any] = {}
            for src_key, db_key in COL_MAP.items():
                if src_key in rec:
                    row[db_key] = self._to_native(rec[src_key])

            if "id" not in row or not row["id"]:
                continue
            row["id"] = str(row["id"])

            self._coerce_record(
                row,
                int_cols=("estimated_value", "asking_price", "value_diff"),
                float_cols=("profit_margin",),
            )
            rows.append(row)

        if not rows:
            return

        self._upsert_batched("bot_opportunities", rows)
        logger.info("Upserted %d rows to 'bot_opportunities'", len(rows))

    def get_all_bot_opportunities(self) -> list[dict[str, Any]]:
        """Fetch all BOT opportunity records.

        Returns:
            List of opportunity row dicts, or an empty list on error.
        """
        try:
            resp = self.client.table("bot_opportunities").select("*").execute()
            return resp.data or []
        except Exception as e:
            logger.error("Failed to fetch bot_opportunities: %s", e)
            return []

    def get_batch_for_evaluation(
        self, batch_size: int = constants.DEFAULT_BATCH_SIZE
    ) -> list[dict[str, Any]]:
        """Fetch the oldest-evaluated BOT players for the next evaluation run.

        Args:
            batch_size: Maximum number of rows to return.

        Returns:
            List of opportunity row dicts ordered by ``last_evaluated_at``
            ascending (nulls first), or an empty list on error.
        """
        try:
            resp = (
                self.client.table("bot_opportunities")
                .select("*")
                .order("last_evaluated_at", desc=False, nullsfirst=True)
                .limit(batch_size)
                .execute()
            )
            return resp.data or []
        except Exception as e:
            logger.error("Failed to fetch bot evaluation batch: %s", e)
            return []

    def clear_bot_opportunities(self) -> None:
        """Delete all rows from the ``bot_opportunities`` table.

        Uses ``neq("id", "0")`` as a filter that matches every real row since
        no player ID will ever be the string ``"0"``.
        """
        try:
            self.client.table("bot_opportunities").delete().neq("id", "0").execute()
            logger.info("Cleared all records from 'bot_opportunities'")
        except Exception as e:
            logger.error("Failed to clear bot_opportunities: %s", e)

    # ------------------------------------------------------------------
    # team_info table
    # ------------------------------------------------------------------

    def upsert_team_info(self, info: dict[str, Any]) -> None:
        """Upsert the single team info row (always ``id=1``).

        Args:
            info: Dict of team info fields from :class:`~src.scrapers.team.TeamInfoScraper`.
        """
        COL_MAP = {
            "team_name": "team_name",
            "manager": "manager",
            "available_funds": "available_funds",
            "financial_situation": "financial_situation",
            "wages_sum": "wages_sum",
            "wage_roof": "wage_roof",
            "academy": "academy",
            "players_count": "players_count",
            "age_average": "age_average",
            "players_value": "players_value",
            "team_reputation": "team_reputation",
            "current_division": "current_division",
            "fan_club_size": "fan_club_size",
        }

        row: dict[str, Any] = {"id": 1}
        for src_key, db_key in COL_MAP.items():
            if src_key in info:
                row[db_key] = str(info[src_key]) if info[src_key] is not None else "N/A"

        try:
            self.client.table("team_info").upsert(row).execute()
            logger.info("Upserted team info to Supabase")
        except Exception as e:
            logger.error("Failed to upsert team_info: %s", e)

    def get_team_info(self) -> dict[str, Any] | None:
        """Fetch the single team info row.

        Returns:
            Team info row dict, or ``None`` if not found or on error.
        """
        try:
            resp = self.client.table("team_info").select("*").eq("id", 1).execute()
            if resp.data:
                return resp.data[0]
            return None
        except Exception as e:
            logger.error("Failed to fetch team_info: %s", e)
            return None
