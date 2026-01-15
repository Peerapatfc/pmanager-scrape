import gspread
from google.oauth2.service_account import Credentials
from src.config import config
from src.core.logger import logger

class SheetManager:
    def __init__(self):
        self.client = self._connect()
        self.spreadsheet = self.client.open_by_key(config.SPREADSHEET_ID)

    def _connect(self):
        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_file(
                config.GOOGLE_CREDENTIALS_FILE, 
                scopes=scopes
            )
            return gspread.authorize(creds)
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            raise

    def get_worksheet(self, sheet_name):
        try:
            return self.spreadsheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            logger.error(f"Worksheet '{sheet_name}' not found.")
            raise

    def upload_data(self, sheet_name, data, columns=None, clear=True):
        """
        Upload list of lists or DataFrame (converted to list)
        """
        ws = self.get_worksheet(sheet_name)
        if clear:
            ws.clear()
        
        payload = []
        if columns:
            payload.append(columns)
        
        payload.extend(data)
        
        try:
            ws.update(payload, value_input_option="USER_ENTERED")
            logger.info(f"Uploaded {len(payload)} rows to '{sheet_name}'")
        except Exception as e:
            logger.error(f"Failed to upload to '{sheet_name}': {e}")

    def get_all_records(self, sheet_name):
        ws = self.get_worksheet(sheet_name)
        return ws.get_all_records()
