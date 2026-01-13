import os
import sys
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    PM_USERNAME = os.getenv("PM_USERNAME")
    PM_PASSWORD = os.getenv("PM_PASSWORD")
    
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
        if not os.path.exists(cls.GOOGLE_CREDENTIALS_FILE):
             # On GitHub Actions, we create this file dynamically, so it might be missing locally if not set up
             print(f"Warning: {cls.GOOGLE_CREDENTIALS_FILE} not found.")

config = Config()
