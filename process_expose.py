import os
import sqlite3
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
IMMO_EMAIL = base64.b64decode(os.getenv("IMMO_EMAIL")).decode("utf-8")
IMMO_PASSWORD = base64.b64decode(os.getenv("IMMO_PASSWORD")).decode("utf-8")
DB_FILE = os.getenv("DB_FILE")
COOKIES_DIR = os.getenv("COOKIES_DIR", "cookies")
os.makedirs(COOKIES_DIR, exist_ok=True)
APPLICATION_TEXT = "Sehr geehrte Damen und Herren,\n\nIch interessiere mich für die von Ihnen angebotene Immobilie. Bitte lassen Sie mir weitere Informationen zukommen.\n\nMit freundlichen Grüßen,\n[Ihr Name]"


PAGE_TITLES = {
    "cookie_wall": "Ich bin kein Roboter",
    "offer_expired": "Angebot nicht gefunden4",
    "offer_deactivated": "Angebot wurde deaktiviert",
    "login_page": "Welcome - ImmobilienScout24",
    "error_page": "Fehler",
    "home_page": "ImmoScout24 – Die Nr. 1 für Immobilien"
}

def wait_for_user():
    input("Please log in and press Enter to continue...")

def save_cookies(driver, site_name):
    cookie_file = os.path.join(COOKIES_DIR, f"{site_name}_cookies.pkl")
    with open(cookie_file, "wb") as f:
        pickle.dump(driver.get_cookies(), f)
    print(f"Cookies saved for {site_name}.")

def load_cookies(driver, site_name):
    cookie_file = os.path.join(COOKIES_DIR, f"{site_name}_cookies.pkl")
    if os.path.exists(cookie_file):
        with open(cookie_file, "rb") as f:
            cookies = pickle.load(f)
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    print(f"Failed to load cookie: {cookie}. Error: {e}")
        print(f"Cookies loaded for {site_name}.")
    else:
        print(f"No cookies found for {site_name}.")

def handle_page_title(driver):
    page_title = driver.title
    print(f"Page title: {page_title}")

    # Check login status based on page elements
    try:
        login_header = driver.find_element(By.CLASS_NAME, "topnavigation__sso-login__header")
        if login_header and "angemeldet als" in login_header.text:
            print("User already logged in.")
            return True
    except Exception:
        pass

    try:
        login_link = driver.find_element(By.CLASS_NAME, "topnavigation__sso-login__middle")
        if login_link and "Anmelden" in login_link.text:
            print("User not logged in. Attempting login.")
            login_link.click()
            if not perform_login(driver):
                print("Login failed. Waiting for manual login.")
                wait_for_user()
#            driver.refresh()
            print("Page reloaded after login.")
            return True
    except Exception:
        pass

    if PAGE_TITLES['cookie_wall'] in page_title:
        print("Cookie wall detected, waiting for user input.")
        wait_for_user()
    elif PAGE_TITLES['offer_expired'] in page_title or PAGE_TITLES['offer_deactivated'] in page_title:
        print("Offer expired or deactivated, skipping.")
        return False
    elif PAGE_TITLES['login_page'] in page_title:
        print("Login page detected, waiting for manual login.")
        wait_for_user()
    elif PAGE_TITLES['error_page'] in page_title or PAGE_TITLES['home_page'] in page_title:
        print("Error or landed on home page, skipping.")
        return False

    print("Login status verified, proceeding.")
    return True


def perform_login(driver):
    try:
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        email_field.send_keys(IMMO_EMAIL)
        print("Email entered successfully.")

        submit_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "submit"))
        )
        submit_button.click()
        print("Email submission successful, waiting for password field.")

        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        password_field.send_keys(IMMO_PASSWORD)
        print("Password entered successfully.")

        remember_me_checkbox = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "label[for='rememberMeCheckBox']"))
        )
        remember_me_checkbox.click()
        print("'Remember Me' checkbox selected.")

        login_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "loginOrRegistration"))
        )
        login_button.click()
        print("Login submitted successfully.")
        return True
    except Exception as e:
        print("Login failed.", e)
        return False
    
def process_immobilienscout24(driver, expose):
    expose_id = expose['expose_id']
    offer_link = f"https://push.search.is24.de/email/expose/{expose_id}"
    print(f"Processing expose from Immobilienscout24: {offer_link}")
    driver.get(offer_link)
    load_cookies(driver, "immobilienscout24")
    WebDriverWait(driver, 120).until(lambda driver: driver.title != "")

    if not handle_page_title(driver):
        return

    def safe_find_element(by, value):
        try:
            return driver.find_element(by, value).text.strip()
        except Exception:
            return "Unknown"

    try:
        offer_title = safe_find_element(By.ID, "expose-title")
        offer_location = safe_find_element(By.CLASS_NAME, "zip-region-and-country")
        agent_name = safe_find_element(By.CLASS_NAME, "truncateChild_5TDve")
        real_estate_agency = safe_find_element(By.CSS_SELECTOR, "p[data-qa='company-name']")
        kalt_price = safe_find_element(By.CLASS_NAME, "is24-preis-value")
        flat_size = safe_find_element(By.CLASS_NAME, "is24qa-wohnflaeche-main")
        number_of_rooms = safe_find_element(By.CLASS_NAME, "is24qa-zi-main")
        nebekosten = safe_find_element(By.CLASS_NAME, "is24qa-nebenkosten")
        total_price = safe_find_element(By.CSS_SELECTOR, "dd.is24qa-gesamtmiete")
        construction_year = safe_find_element(By.CLASS_NAME, "is24qa-baujahr")
        description = safe_find_element(By.CLASS_NAME, "is24qa-objektbeschreibung")
        area_description = safe_find_element(By.CLASS_NAME, "is24qa-lage")

        # Update database before attempting login
        update_expose(
            expose_id,
            title=offer_title,
            location=offer_location,
            agent_name=agent_name,
            real_estate_agency=real_estate_agency,
            price_kalt=kalt_price,
            square_meters=flat_size,
            number_of_rooms=number_of_rooms,
            nebekosten=nebekosten,
            price_warm=total_price,
            construction_year=construction_year,
            description=description,
            neighborhood=area_description,
        )
        print(f"Expose {expose_id} updated in the database.")

        try:
            message_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "Button_button-primary__6QTnx"))
            )
            message_button.click()
            print("Message button found and clicked successfully.")

            if "Welcome - ImmobilienScout24" in driver.title:
                print("User not logged in. Waiting for manual login.")
                wait_for_user()

            if "MieterPlus freischalten | ImmoScout24" in driver.title:
                print("MieterPlus page detected. Skipping expose.")
                return

            message_label = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "label[for='message']"))
            )
            message_box = driver.find_element(By.ID, "message")
            message_box.clear()
            message_box.send_keys(APPLICATION_TEXT)
            print("Application text entered successfully.")

            send_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button[type='submit'].Button_button-primary__6QTnx"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", send_button)
            send_button.click()
            print("Message sent, waiting for confirmation.")

            confirmation_message = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//h2[text()='Nachricht gesendet']"))
            )
            if confirmation_message:
                mark_expose_as_processed(expose_id)
                print(f"Expose {expose_id} marked as processed.")

        except Exception as e:
            print("Failed to send message or fill the form.", e)

    except Exception as e:
        print("Error while extracting additional data.", e)

    save_cookies(driver, "immobilienscout24")



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

    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.maximize_window()
    return driver

def process_all_exposes():
    exposes = get_unprocessed_exposes()
    if not exposes:
        print("No unprocessed exposes found.")
        return
    stealthdriver = get_stealth_browser()

    for expose in exposes:
        source_key = expose['source']
        print(f"Debug: Processing source key: {source_key}")
        process_function_name = f"process_{source_key}"
        if process_function_name in globals():
            globals()[process_function_name](stealthdriver, expose)
        else:
            print(f"Processing function {process_function_name} unknown")

    stealthdriver.quit()
