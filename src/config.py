import os
import sys
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    PM_USERNAME = os.getenv("PM_USERNAME")
    PM_PASSWORD = os.getenv("PM_PASSWORD")
    
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    # Google Sheets (legacy, kept for backward compatibility)
    GOOGLE_CREDENTIALS_FILE = "credentials.json"
    SPREADSHEET_ID = "1F8FWV9w1gNAGbGDd6RG929dx2jAcM-N6p2ve9fOwSfU"
    SHEET_NAME_ALL_PLAYERS = "All Players"
    SHEET_NAME_TRANSFER_INFO = "Transfer Info"
    
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    HEADLESS_MODE = True

    @classmethod
    def validate(cls):
        if not cls.PM_USERNAME or not cls.PM_PASSWORD:
            print("Error: PM_USERNAME or PM_PASSWORD not set in .env")
            sys.exit(1)
        if not cls.SUPABASE_URL or not cls.SUPABASE_KEY:
            print("Error: SUPABASE_URL or SUPABASE_KEY not set in .env")
            sys.exit(1)

config = Config()
