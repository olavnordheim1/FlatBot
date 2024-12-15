import os
import time
import random
import base64
import pickle
from database import get_unprocessed_exposes, update_expose, mark_expose_as_processed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
COOKIES_DIR = os.getenv("COOKIES_DIR", "cookies")
os.makedirs(COOKIES_DIR, exist_ok=True)

def get_stealth_browser():
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
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.maximize_window()
    return driver

def kill(driver):
    driver.driver.quit()

def wait_for_user():
    input("Please log in and press Enter to continue...")
    
def random_wait(driver, min_seconds=2, max_seconds=5):
    wait_time = random.uniform(min_seconds, max_seconds)
    print(f"Waiting for {wait_time:.2f} seconds...")
    time.sleep(wait_time)

def safe_find_element(driver, by, value):
    try:
        return driver.find_element(by, value).text.strip()
    except Exception:
        return "Unknown"
    
def random_mouse_movements(driver, element):
    action = ActionChains(driver.driver)
    for _ in range(random.randint(2, 5)):
        offset_x = random.randint(-100, 100)
        offset_y = random.randint(-100, 100)
        action.move_to_element_with_offset(element, offset_x, offset_y).perform()
        print(f"Moved mouse to offset ({offset_x}, {offset_y})")
        driver.random_wait(0.5, 1.5)

def random_scroll(driver):
    scroll_amount = random.randint(-300, 300)
    driver.driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
    print(f"Scrolled by {scroll_amount} pixels")
    driver.random_wait(0.5, 1.5)

def perform_random_action(driver):
    actions = [
        driver.random_scroll,
        lambda: driver.random_wait(42, 15),
    ]
    action = random.choice(actions)
    action()

def save_cookies(driver, site_name):
    cookie_file = os.path.join(COOKIES_DIR, f"{site_name}_cookies.pkl")
    with open(cookie_file, "wb") as f:
        pickle.dump(driver.driver.get_cookies(), f)
    print(f"Cookies saved for {site_name}.")

def load_cookies(driver, site_name):
    cookie_file = os.path.join(COOKIES_DIR, f"{site_name}_cookies.pkl")
    if os.path.exists(cookie_file):
        with open(cookie_file, "rb") as f:
            cookies = pickle.load(f)
            for cookie in cookies:
                try:
                    driver.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"Failed to load cookie: {cookie}. Error: {e}")
        print(f"Cookies loaded for {site_name}.")
    else:
        print(f"No cookies found for {site_name}.")
