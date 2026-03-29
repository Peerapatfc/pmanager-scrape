"""
Telegram notification service for pmanager-scrape.

Provides :class:`TelegramBot` for sending messages to a Telegram chat.
Messages are first attempted with Markdown formatting; on failure the bot
falls back to plain text automatically.
"""

import requests

from src.config import config
from src.core.logger import logger

#: Default timeout (seconds) for Telegram API HTTP requests.
_REQUEST_TIMEOUT: int = 10


class TelegramBot:
    """Sends messages to a Telegram chat via the Bot API."""

    def __init__(self) -> None:
        self.bot_token: str | None = config.TELEGRAM_BOT_TOKEN
        self.chat_id: str | None = config.TELEGRAM_CHAT_ID

    def send_message(self, message: str) -> bool:
        """Send a message to the configured Telegram chat.

        Attempts Markdown formatting first. If the API rejects the message
        (e.g. due to malformed Markdown), retries as plain text.

        Args:
            message: Message body to send. May contain Telegram Markdown
                syntax (``*bold*``, ``_italic_``, etc.).

        Returns:
            ``True`` if the message was delivered successfully, ``False``
            otherwise.
        """
        if not self.bot_token or not self.chat_id:
            logger.error("Telegram credentials not configured — message not sent.")
            return False

        api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
        }

        try:
            response = requests.post(api_url, json=payload, timeout=_REQUEST_TIMEOUT)
            if response.status_code == 200:
                logger.info("Telegram message sent (Markdown).")
                return True

            # Markdown failed — retry without parse_mode
            logger.warning(
                "Markdown send failed (%s). Retrying as plain text...",
                response.text,
            )
            del payload["parse_mode"]
            response = requests.post(api_url, json=payload, timeout=_REQUEST_TIMEOUT)
            if response.status_code == 200:
                logger.info("Telegram message sent (plain text).")
                return True

            logger.error("Plain text send also failed: %s", response.text)
            return False

        except Exception as e:
            logger.error("Error sending Telegram message: %s", e, exc_info=True)
            return False
