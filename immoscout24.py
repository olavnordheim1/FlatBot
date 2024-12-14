import os
import time
import random
import base64
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
IMMO_EMAIL = base64.b64decode(os.getenv("IMMO_EMAIL")).decode("utf-8")
IMMO_PASSWORD = base64.b64decode(os.getenv("IMMO_PASSWORD")).decode("utf-8")

def get_stealth_browser():
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-notifications")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36")
    width = random.randint(1024, 1920)
    height = random.randint(768, 1080)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_window_size(width, height)
    return driver

def human_like_delay():
    time.sleep(random.uniform(2, 5))

def login_immoscout():
    driver = get_stealth_browser()
    driver.get("https://www.immobilienscout24.de/")
    print("Page loaded.")

    try:
        # Accept cookies with retries
        cookie_buttons = [
            "//button[contains(text(),'Alle akzeptieren')]",
            "//button[@data-testid='uc-accept-all-button']"
        ]
        for _ in range(3):
            for btn_xpath in cookie_buttons:
                try:
                    WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, btn_xpath))
                    ).click()
                    print("Cookies accepted.")
                    break
                except Exception as e:
                    print(f"Retrying cookie acceptance with {btn_xpath}...")
                    time.sleep(3)
            else:
                continue
            break
        else:
            print("Failed to accept cookies after multiple attempts.")
            driver.save_screenshot("cookie_error.png")

        # Click login button
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".topnavigation__sso-login__middle:nth-child(1)"))
        ).click()
        print("Login page opened.")

        # Enter email
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        email_input.clear()
        email_input.send_keys(IMMO_EMAIL)
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "submit"))
        ).click()
        print("Email submitted.")

        # Enter password
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        password_input.clear()
        password_input.send_keys(IMMO_PASSWORD)
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "loginOrRegistration"))
        ).click()
        print("Logged in successfully.")

    except Exception as e:
        import traceback
        print(f"Login process failed: {e}")
        driver.save_screenshot("error_screenshot.png")
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    login_immoscout()
