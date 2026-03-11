from supabase import create_client
from src.config import config
from src.core.logger import logger


class SupabaseManager:
    def __init__(self):
        self.client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

    # ── Players (replaces "All Players" sheet) ──

    def upsert_players(self, records: list[dict]):
        """
        Batch upsert player records into the `players` table.
        
        Accepts raw dicts from the scraper. Known columns are mapped
        to their DB columns; all remaining keys are packed into `skills` JSONB.
        """
        KNOWN_COLS = {
            "id", "name", "position", "age", "nationality",
            "Quality", "Potential", "Affected Quality",
            "bids_count", "bids_avg", "deadline", "url",
            "last_transfer_price", "sale_to_bid_ratio",
        }
        
        rows = []
        for rec in records:
            row = {}
            skills = {}
            
            for key, val in rec.items():
                # Map column names to DB-safe lowercase
                db_key = key.lower().replace(" ", "_")
                
                if key in KNOWN_COLS or db_key in {
                    "id", "name", "position", "age", "nationality",
                    "quality", "potential", "affected_quality",
                    "bids_count", "bids_avg", "deadline", "url",
                    "last_transfer_price", "sale_to_bid_ratio",
                }:
                    row[db_key] = self._to_native(val)
                else:
                    # Everything else goes into skills JSONB
                    skills[key] = self._to_native(val)
            
            row["skills"] = skills
            
            # Ensure id exists
            if "id" not in row or not row["id"]:
                continue
            
            # Coerce types
            row["id"] = str(row["id"])
            if "age" in row:
                try:
                    row["age"] = int(row["age"]) if row["age"] else None
                except (ValueError, TypeError):
                    row["age"] = None
            
            rows.append(row)
        
        if not rows:
            return
        
        # Supabase upsert in batches of 500
        for i in range(0, len(rows), 500):
            batch = rows[i:i + 500]
            try:
                self.client.table("players").upsert(batch).execute()
            except Exception as e:
                logger.error(f"Failed to upsert players batch {i}: {e}")
        
        logger.info(f"Upserted {len(rows)} rows to 'players'")

    def get_all_players(self) -> list[dict]:
        """Fetch all player records."""
        try:
            resp = self.client.table("players").select("*").execute()
            return resp.data or []
        except Exception as e:
            logger.error(f"Failed to fetch players: {e}")
            return []

    def update_player(self, player_id: str, data: dict):
        """Update specific fields on a single player."""
        clean = {k: self._to_native(v) for k, v in data.items()}
        try:
            self.client.table("players").update(clean).eq("id", str(player_id)).execute()
        except Exception as e:
            logger.error(f"Failed to update player {player_id}: {e}")

    # ── Transfer Listings (replaces "Transfer Info" sheet) ──

    def upsert_transfer_listings(self, records: list[dict]):
        """Batch upsert transfer listing records."""
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
        
        rows = []
        for rec in records:
            row = {}
            for src_key, db_key in COL_MAP.items():
                if src_key in rec:
                    row[db_key] = self._to_native(rec[src_key])
            
            if "id" not in row or not row["id"]:
                continue
            row["id"] = str(row["id"])
            
            # Coerce numeric types
            if "age" in row:
                try:
                    row["age"] = int(row["age"]) if row["age"] else None
                except (ValueError, TypeError):
                    row["age"] = None
            for num_col in ["estimated_value", "asking_price", "value_diff"]:
                if num_col in row:
                    try:
                        row[num_col] = int(row[num_col]) if row[num_col] != "" else 0
                    except (ValueError, TypeError):
                        row[num_col] = 0
            for float_col in ["roi", "forecast_sell", "forecast_profit"]:
                if float_col in row:
                    try:
                        row[float_col] = float(row[float_col]) if row[float_col] != "" else 0.0
                    except (ValueError, TypeError):
                        row[float_col] = 0.0
            
            rows.append(row)
        
        if not rows:
            return
        
        for i in range(0, len(rows), 500):
            batch = rows[i:i + 500]
            try:
                self.client.table("transfer_listings").upsert(batch).execute()
            except Exception as e:
                logger.error(f"Failed to upsert transfer_listings batch {i}: {e}")
        
        logger.info(f"Upserted {len(rows)} rows to 'transfer_listings'")

    def get_all_transfer_listings(self) -> list[dict]:
        """Fetch all transfer listing records."""
        try:
            resp = self.client.table("transfer_listings").select("*").execute()
            return resp.data or []
        except Exception as e:
            logger.error(f"Failed to fetch transfer_listings: {e}")
            return []

    # ── Team Info (replaces "Team Info" sheet) ──

    def upsert_team_info(self, info: dict):
        """Upsert a single team info row (always id=1)."""
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
        
        row = {"id": 1}
        for src_key, db_key in COL_MAP.items():
            if src_key in info:
                row[db_key] = str(info[src_key]) if info[src_key] is not None else "N/A"
        
        try:
            self.client.table("team_info").upsert(row).execute()
            logger.info("Upserted team info to Supabase")
        except Exception as e:
            logger.error(f"Failed to upsert team_info: {e}")

    def get_team_info(self) -> dict | None:
        """Fetch the single team info row."""
        try:
            resp = self.client.table("team_info").select("*").eq("id", 1).execute()
            if resp.data:
                return resp.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to fetch team_info: {e}")
            return None

    # ── Helpers ──

    @staticmethod
    def _to_native(val):
        """Convert numpy/pandas types to native Python types."""
        try:
            import numpy as np
            if isinstance(val, np.ndarray):
                return val.tolist()
            if isinstance(val, (np.integer,)):
                return int(val)
            if isinstance(val, (np.floating,)):
                v = float(val)
                if np.isnan(v) or np.isinf(v):
                    return 0
                return v
            if isinstance(val, (np.bool_,)):
                return bool(val)
        except ImportError:
            pass
        
        if val is None:
            return None
        return val
