import requests
from src.config import config
from src.core.logger import logger

class TelegramBot:
    def __init__(self):
        self.bot_token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID

    def send_message(self, message):
        """Send message to Telegram with retry logic (Markdown -> Plain Text)"""
        if not self.bot_token or not self.chat_id:
            logger.error("Telegram credentials not found in env.")
            return

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": message, "parse_mode": "Markdown"}

        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                logger.info("Message sent to Telegram (Markdown)!")
            else:
                logger.warning(f"Failed to send Markdown: {response.text}. Retrying as Plain Text...")
                del payload["parse_mode"]
                response = requests.post(url, json=payload)
                if response.status_code == 200:
                    logger.info("Message sent to Telegram (Plain Text)!")
                else:
                    logger.error(f"Failed to send Plain Text: {response.text}")
        except Exception as e:
            logger.error(f"Error sending to Telegram: {e}")
