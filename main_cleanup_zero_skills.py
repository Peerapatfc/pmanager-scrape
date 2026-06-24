"""Remove players with all-zero skills (unscouted) from the players table."""

from src.config import config
from src.services.supabase_client import SupabaseManager


def main() -> None:
    config.validate()
    db = SupabaseManager()
    deleted = db.delete_zero_skill_players()
    print(f"Done — deleted {deleted} zero-skill players.")


if __name__ == "__main__":
    main()
