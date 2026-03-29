"""
Base scraper providing Playwright browser setup and PManager login.

All scraper classes should extend :class:`BaseScraper`. It handles browser
lifecycle and authentication so subclasses can focus on page-specific logic.

Usage as a context manager (recommended — ensures browser cleanup on error)::

    with TransferScraper() as scraper:
        scraper.login(username, password)
        results = scraper.get_listings()
"""

from __future__ import annotations

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from src.core.logger import logger


class BaseScraper:
    """Manages a Playwright browser instance and PManager login session."""

    def __init__(self, base_url: str = "https://www.pmanager.org") -> None:
        """Initialise the scraper with the target base URL.

        Args:
            base_url: Root URL of the PManager site.
        """
        self.base_url: str = base_url
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.page: Page | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self, headless: bool = True) -> None:
        """Launch the Chromium browser.

        Args:
            headless: Run without a visible window (default ``True``).
        """
        logger.info("Starting browser...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.page = self.browser.new_page()

    def stop(self) -> None:
        """Close the browser and stop the Playwright engine."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Browser stopped.")

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> BaseScraper:
        self.start()
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.stop()

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def login(self, username: str, password: str) -> None:
        """Authenticate with PManager.

        Navigates to the login page and submits credentials if the login form
        is present. Assumes an existing session if the form is not found.

        Args:
            username: PManager account username.
            password: PManager account password.

        Raises:
            Exception: Re-raises any Playwright error encountered during login.
        """
        try:
            logger.info("Logging in as %s...", username)
            self.page.goto(f"{self.base_url}/default.asp")

            if self.page.query_selector("#utilizador"):
                self.page.fill("#utilizador", username)
                self.page.fill("#password", password)
                self.page.click(".btn-login")
                self.page.wait_for_load_state("networkidle")
                logger.info("Login submitted.")
            else:
                logger.info("Login form not found. Assuming already logged in.")

        except Exception as e:
            logger.error("Login failed: %s", e, exc_info=True)
            raise
