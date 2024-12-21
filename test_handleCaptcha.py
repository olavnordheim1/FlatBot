import os
import time
from datetime import datetime
import importlib
import logging
from modules.Database import ExposeDB, Expose
from modules.EmailFetcher import EmailFetcher
from modules.StealthBrowser import StealthBrowser
from modules.Immobilienscout24_processor import Immobilienscout24_processor
from selenium.webdriver.support.ui import WebDriverWait


logger = logging.getLogger(__name__)
log_level = logging.INFO

test_url = "https://www.immobilienscout24.de/expose/156170682"

def init_log():    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    # Generate log file name
    current_time = datetime.now()
    log_file = f"test_handleCaptcha_{current_time.day}_{current_time.month}_{current_time.year}.log"
    log_file_path = os.path.join(log_dir, log_file)
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file_path),
            logging.StreamHandler()
        ]
    )

def main():
    init_log()
    logging.warning("Testing handle captcha")
    browser = StealthBrowser()
    processor = Immobilienscout24_processor(browser)
    browser.get(test_url)
    # Explicit wait for the title to not be empty
    WebDriverWait(browser, 10).until(
        lambda d: d.title.strip() != ""
    )
    page_title = browser.title
    logger.info(f"Page title: {page_title}")
    if processor.immo_page_titles['captcha_wall'] in page_title:
            processor._handle_captcha()
    else:
         browser.refresh()
    input("Press any key to exit....")
    browser.kill()

if __name__ == "__main__":
    main()