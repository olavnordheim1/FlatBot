import os
import time
import base64
import modules.StealthBrowser as StealthBrowser
import modules.Database as database
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from BaseExposeProcessor import BaseExposeProcessor

class ImmobilienscoutProcessor(BaseExposeProcessor):
    NAME = "Immobilienscout24"
    DOMAIN = "immobilienscout24.de"

    def __init__(self, email=None, password=None, db_file=None, StealthBrowser=None):
        super().__init__(self.NAME, self.DOMAIN, email, password, db_file, StealthBrowser)
        load_dotenv()
        self.email = email or base64.b64decode(os.getenv("IMMO_EMAIL")).decode("utf-8")
        self.password = password or base64.b64decode(os.getenv("IMMO_PASSWORD")).decode("utf-8")
        self.db_file = db_file or os.getenv("DB_FILE")
        self.application_text = os.getenv("APPLICATION_TEXT", "Sehr geehrte Damen und Herren,\n\nIch interessiere mich für die von Ihnen angebotene Immobilie. Bitte lassen Sie mir weitere Informationen zukommen.\n\nMit freundlichen Grüßen,\n[Ihr Name]")

    def extract_expose_link(self, subject, email_body):
        pattern = re.compile(r"https:\/\/[a-zA-Z0-9./?=&_-]*expose/(\d+)")
        return list(set(pattern.findall(email_body)))

    def generate_expose_link(self, expose):
        expose_id = expose['expose_id']
        return f"https://push.search.is24.de/email/expose/{expose_id}"

    def login(self, driver):
        try:
            login_link = driver.find_element(By.CLASS_NAME, "topnavigation__sso-login__middle")
            if login_link and "Anmelden" in login_link.text:
                login_link.click()
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(self.email)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "submit"))).click()
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "password"))).send_keys(self.password)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "loginOrRegistration"))).click()
                StealthBrowser.save_cookies(driver, "immobilienscout24")
                driver.refresh()
                return True
        except Exception as e:
            print("Login failed.", e)
            return False

    def handle_page(self, driver, expose_id):
        page_title = driver.title
        print(f"Page title: {page_title}")
        if "Ich bin kein Roboter" in page_title:
            driver.wait_for_user()
        elif "Angebot nicht gefunden" in page_title or "Angebot wurde deaktiviert" in page_title:
            database.mark_expose_as_processed(expose_id)
            return False
        elif "Welcome - ImmobilienScout24" in page_title:
            return self.login(driver)
        elif "Fehler" in page_title or "ImmoScout24 – Die Nr. 1 für Immobilien" in page_title:
            return False
        return self.scrape_expose(driver, expose_id) and self.apply_for_offer(driver, expose_id)

    def scrape_expose(self, driver, expose_id):
        try:
            offer_title = StealthBrowser.safe_find_element(driver, By.ID, "expose-title")
            if offer_title != "Unknown":
                database.update_expose(
                    expose_id,
                    title=offer_title,
                    location=StealthBrowser.safe_find_element(driver, By.CLASS_NAME, "zip-region-and-country"),
                    agent_name=StealthBrowser.safe_find_element(driver, By.CLASS_NAME, "truncateChild_5TDve"),
                    real_estate_agency=StealthBrowser.safe_find_element(driver, By.CSS_SELECTOR, "p[data-qa='company-name']"),
                    price_kalt=StealthBrowser.safe_find_element(driver, By.CLASS_NAME, "is24-preis-value"),
                    square_meters=StealthBrowser.safe_find_element(driver, By.CLASS_NAME, "is24qa-wohnflaeche-main"),
                    number_of_rooms=StealthBrowser.safe_find_element(driver, By.CLASS_NAME, "is24qa-zi-main"),
                    nebekosten=StealthBrowser.safe_find_element(driver, By.CLASS_NAME, "is24qa-nebenkosten"),
                    price_warm=StealthBrowser.safe_find_element(driver, By.CSS_SELECTOR, "dd.is24qa-gesamtmiete"),
                    construction_year=StealthBrowser.safe_find_element(driver, By.CLASS_NAME, "is24qa-baujahr"),
                    description=StealthBrowser.safe_find_element(driver, By.CLASS_NAME, "is24qa-objektbeschreibung"),
                    neighborhood=StealthBrowser.safe_find_element(driver, By.CLASS_NAME, "is24qa-lage"),
                )
                return True
        except Exception:
            print("Scraping failed.")
            return False

    def apply_for_offer(self, driver, expose_id):
        try:
            message_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "Button_button-primary__6QTnx"))
            )
            message_button.click()
            message_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "message"))
            )
            message_box.clear()
            message_box.send_keys(APPLICATION_TEXT)
            send_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button[type='submit'].Button_button-primary__6QTnx"))
            )
            send_button.click()
            database.mark_expose_as_processed(expose_id)
            return True
        except Exception as e:
            print("Application failed.", e)
            return False
