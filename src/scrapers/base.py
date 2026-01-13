from playwright.sync_api import sync_playwright
from src.core.logger import logger

class BaseScraper:
    def __init__(self, base_url="https://www.pmanager.org"):
        self.base_url = base_url
        self.playwright = None
        self.browser = None
        self.page = None

    def start(self, headless=True):
        logger.info("Starting browser...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.page = self.browser.new_page()

    def stop(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Browser stopped.")

    def login(self, username, password):
        try:
            logger.info(f"Logging in as {username}...")
            self.page.goto(f"{self.base_url}/default.asp")
            
            # Check if login form exists
            if self.page.query_selector("#utilizador"):
                self.page.fill("#utilizador", username)
                self.page.fill("#password", password)
                self.page.click(".btn-login")
                self.page.wait_for_load_state("networkidle")
                logger.info("Login submitted.")
            else:
                logger.info("Login form not found. Assuming already logged in.")
                
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise
