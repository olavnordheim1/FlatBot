import os
import time
import random
import base64
import pickle
from modules.Database import ExposeDB, Expose
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from dotenv import load_dotenv

class StealthBrowser(webdriver.Chrome):
    def __init__(self):
        # Load environment variables
        load_dotenv()
        self.cookies_dir = os.getenv("COOKIES_DIR", "cookies")
        os.makedirs(self.cookies_dir, exist_ok=True)

        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-notifications")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--disable-web-security")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
        )
        super().__init__(service=Service(ChromeDriverManager().install()), options=options)
        self.maximize_window()

    def kill(self):
        self.quit()

    def wait_for_user(self):
        input("Please log in and press Enter to continue...")

    def random_wait(self, min_seconds=2, max_seconds=5):
        wait_time = random.uniform(min_seconds, max_seconds)
        print(f"Waiting for {wait_time:.2f} seconds...")
        time.sleep(wait_time)

    def safe_find_element(self, by, value):
        try:
            return self.find_element(by, value).text.strip()
        except Exception:
            return "Unknown"

    def random_mouse_movements(self, element):
        action = ActionChains(self)
        for _ in range(random.randint(2, 5)):
            offset_x = random.randint(-100, 100)
            offset_y = random.randint(-100, 100)
            action.move_to_element_with_offset(element, offset_x, offset_y).perform()
            print(f"Moved mouse to offset ({offset_x}, {offset_y})")
            self.random_wait(0.5, 1.5)

    def random_scroll(self):
        scroll_amount = random.randint(-300, 300)
        self.execute_script(f"window.scrollBy(0, {scroll_amount})")
        print(f"Scrolled by {scroll_amount} pixels")
        self.random_wait(0.5, 1.5)

    def perform_random_action(self):
        actions = [
            self.random_scroll,
            lambda: self.random_wait(42, 15),
        ]
        action = random.choice(actions)
        action()

    def save_cookies(self, site_name):
        cookie_file = os.path.join(self.cookies_dir, f"{site_name}_cookies.pkl")
        with open(cookie_file, "wb") as f:
            pickle.dump(self.get_cookies(), f)
        print(f"Cookies saved for {site_name}.")

    def load_cookies(self, site_name):
        cookie_file = os.path.join(self.cookies_dir, f"{site_name}_cookies.pkl")
        if os.path.exists(cookie_file):
            with open(cookie_file, "rb") as f:
                cookies = pickle.load(f)
                for cookie in cookies:
                    try:
                        self.add_cookie(cookie)
                    except Exception as e:
                        print(f"Failed to load cookie: {cookie}. Error: {e}")
            print(f"Cookies loaded for {site_name}.")
        else:
            print(f"No cookies found for {site_name}.")
