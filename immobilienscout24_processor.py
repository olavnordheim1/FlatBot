import os
import time
import base64
import stealth_browser
import database
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
IMMO_EMAIL = base64.b64decode(os.getenv("IMMO_EMAIL")).decode("utf-8")
IMMO_PASSWORD = base64.b64decode(os.getenv("IMMO_PASSWORD")).decode("utf-8")
DB_FILE = os.getenv("DB_FILE")

APPLICATION_TEXT = os.getenv("APPLICATION_TEXT", "Sehr geehrte Damen und Herren,\n\nIch interessiere mich für die von Ihnen angebotene Immobilie. Bitte lassen Sie mir weitere Informationen zukommen.\n\nMit freundlichen Grüßen,\n[Ihr Name]")


immo_page_titles = {
    "cookie_wall": "Ich bin kein Roboter",
    "offer_expired": "Angebot nicht gefunden4",
    "offer_deactivated": "Angebot wurde deaktiviert",
    "login_page": "Welcome - ImmobilienScout24",
    "error_page": "Fehler",
    "home_page": "ImmoScout24 – Die Nr. 1 für Immobilien"
}

def generate_immobilienscout_link(expose):
    expose_id = expose['expose_id']
    offer_link = f"https://push.search.is24.de/email/expose/{expose_id}"
    return offer_link


def handle_page_title(stealth_browser):
    page_title = stealth_browser.title
    print(f"Page title: {page_title}")

    if immo_page_titles['cookie_wall'] in page_title:
        print("Cookie wall detected, waiting for user input.")
        stealth_browser.wait_for_user()
    elif immo_page_titles['offer_expired'] in page_title or immo_page_titles['offer_deactivated'] in page_title:
        print("Offer expired or deactivated, skipping.")
        return False
    elif immo_page_titles['login_page'] in page_title:
        print("Login page detected, waiting for manual login.")
        stealth_browser.wait_for_user()
    elif immo_page_titles['error_page'] in page_title or immo_page_titles['home_page'] in page_title:
        print("Error or landed on home page, skipping.")
        return False
        # Check login status based on page elements
    try:
        login_header = stealth_browser.find_element(By.CLASS_NAME, "topnavigation__sso-login__header")
        if login_header and "angemeldet als" in login_header.text:
            print("User already logged in.")
            return True
    except Exception:
        pass

    try:
        login_link = stealth_browser.find_element(By.CLASS_NAME, "topnavigation__sso-login__middle")
        if login_link and "Anmelden" in login_link.text:
            print("User not logged in. Attempting login.")
            login_link.click()
            if not perform_login(stealth_browser):
                print("Login failed. Waiting for manual login.")
                stealth_browser.wait_for_user()
            stealth_browser.refresh()
            print("Page reloaded after login.")
            return True
    except Exception:
        pass

    stealth_browser.perform_random_action()

    print("Login status verified, proceeding.")
    return True


def perform_login(stealth_browser):
    try:
        email_field = WebDriverWait(stealth_browser, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        email_field.send_keys(IMMO_EMAIL)
        print("Email entered successfully.")
        stealth_browser.perform_random_action(stealth_browser)

        submit_button = WebDriverWait(stealth_browser, 10).until(
            EC.presence_of_element_located((By.ID, "submit"))
        )
        stealth_browser.random_mouse_movements(submit_button)
        submit_button.click()
        print("Email submission successful, waiting for password field.")

        password_field = WebDriverWait(stealth_browser, 10).until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        password_field.send_keys(IMMO_PASSWORD)
        print("Password entered successfully.")
        stealth_browser.perform_random_action()
        remember_me_checkbox = WebDriverWait(stealth_browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "label[for='rememberMeCheckBox']"))
        )
        stealth_browser.random_mouse_movements( remember_me_checkbox)
        #remember_me_checkbox.click()
        #print("'Remember Me' checkbox selected.")
        stealth_browser.perform_random_action()
        login_button = WebDriverWait(stealth_browser, 10).until(
            EC.presence_of_element_located((By.ID, "loginOrRegistration"))
        )
        stealth_browser.random_mouse_movements(login_button)
        login_button.click()
        print("Login submitted successfully.")
        return True
    except Exception as e:
        print("Login failed.", e)
        return False
    
def scrape_expose(stealth_browser, expose_id):
    def safe_find_element(by, value):
        try:
            return stealth_browser.find_element(by, value).text.strip()
        except Exception:
            return "Unknown"

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

    database.update_expose(
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
    stealth_browser.perform_random_action()

def click_message_button(stealth_browser):
    try:
        message_button = WebDriverWait(stealth_browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "Button_button-primary__6QTnx"))
        )
        stealth_browser.perform_random_action()
        message_button.click()
        print("Message button found and clicked successfully.")
        return True
    except Exception as e:
        print("Failed to find or click message button.", e)
        return False

def handle_message_form(stealth_browser, expose_id):
    if "Welcome - ImmobilienScout24" in stealth_browser.title:
        print("User not logged in. Waiting for manual login.")
        stealth_browser.wait_for_user()
        return False

    if "MieterPlus freischalten | ImmoScout24" in stealth_browser.title:
        print("MieterPlus page detected. Skipping expose.")
        database.mark_expose_as_processed(expose_id)
        print(f"Expose {expose_id} marked as processed.")
        return True

    try:
        message_label = WebDriverWait(stealth_browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "label[for='message']"))
        )
        message_box = stealth_browser.find_element(By.ID, "message")
        message_box.clear()
        message_box.send_keys(APPLICATION_TEXT)
        print("Application text entered successfully.")
        stealth_browser.perform_random_action()

        send_button = WebDriverWait(stealth_browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button[type='submit'].Button_button-primary__6QTnx"))
        )
        stealth_browser.execute_script("arguments[0].scrollIntoView(true);", send_button)
        send_button.click()
        print("Message sent, waiting for confirmation.")

        confirmation_message = WebDriverWait(stealth_browser, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[text()='Nachricht gesendet']"))
        )
        if confirmation_message:
            database.mark_expose_as_processed(expose_id)
            print(f"Expose {expose_id} marked as processed.")
            return True

    except Exception as e:
        print("Failed to send message or fill the form.", e)
    return False

def process_expose(stealth_browser, expose):
    offer_link = generate_immobilienscout_link(expose)
    print(f"Processing expose from Immobilienscout24: {offer_link}")
    expose_id = expose['expose_id']
    stealth_browser.get(offer_link)
    stealth_browser.load_cookies(stealth_browser, "immobilienscout24")
    WebDriverWait(stealth_browser, 120).until(lambda driver: driver.title != "")

    if not handle_page_title(stealth_browser):
        return
    
    stealth_browser.get(offer_link)
    stealth_browser.perform_random_action()
    scrape_expose(stealth_browser, expose_id)
    stealth_browser.perform_random_action()
    if click_message_button(stealth_browser):
        stealth_browser.random_wait(min_seconds=2, max_seconds=7)
        try:
            handle_message_form(stealth_browser, expose_id)
        except Exception as e:
            print("Error while extracting additional data.", e)

    stealth_browser.save_cookies(stealth_browser, "immobilienscout24")