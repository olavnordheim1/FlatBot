import os
import time
import base64
import modules.StealthBrowser as StealthBrowser
import modules.database as database
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

def extract_expose_link(self, subject, email_body):
    """Extract unique expose links from the email body specific to Immobilienscout24."""
    pattern = re.compile(r"https:\/\/[a-zA-Z0-9./?=&_-]*expose/(\d+)")
    return list(set(pattern.findall(email_body)))


def generate_expose_link(expose):
    expose_id = expose['expose_id']
    offer_link = f"https://push.search.is24.de/email/expose/{expose_id}"
    return offer_link

def check_login(driver):
    # Check login status based on page elements
    try:
        login_header = driver.find_element(By.CLASS_NAME, "topnavigation__sso-login__header")
        if login_header and "angemeldet als" in login_header.text:
            print("User already logged in.")
            return True
    except Exception:
        print("User does not seems to be logged in")
        return False

def perform_login(driver):
    try:
        login_link = driver.find_element(By.CLASS_NAME, "topnavigation__sso-login__middle")
        if login_link and "Anmelden" in login_link.text:
            print("User not logged in. Attempting login.")
            login_link.click()
            try:
                StealthBrowser.random_wait(driver)
                email_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "username"))
                )
                email_field.send_keys(IMMO_EMAIL)
                print("Email entered successfully.")
                StealthBrowser.perform_random_action(driver)

                submit_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "submit"))
                )
                StealthBrowser.random_mouse_movements(submit_button)
                submit_button.click()
                print("Email submission successful, waiting for password field.")

                StealthBrowser.random_wait(driver)
                password_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "password"))
                )
                password_field.send_keys(IMMO_PASSWORD)
                print("Password entered successfully.")
                StealthBrowser.perform_random_action(driver)

                remember_me_checkbox = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "label[for='rememberMeCheckBox']"))
                )
                StealthBrowser.random_mouse_movements( driver, remember_me_checkbox)
                #remember_me_checkbox.click()
                #print("'Remember Me' checkbox selected.")
                StealthBrowser.perform_random_action(driver)
                login_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "loginOrRegistration"))
                )
                StealthBrowser.random_mouse_movements(driver, login_button)
                login_button.click()
                print("Login submitted successfully.")

                ## TO-DO validate success
                StealthBrowser.save_cookies(driver, "immobilienscout24")
                driver.refresh()
                print("Page reloaded after login.")
                return True
            except Exception as e:
                print("Login failed.", e)
                #browser_helpers.wait_for_user()
                # TO-DO Notify user
                return False                           
    except Exception:
        print("Login button not found.", e)
        #browser_helpers.wait_for_user()
        # TO-DO Notify user
        return False  
    
def scrape_expose(driver, expose_id):
    # Check title
    try:
        offer_title = StealthBrowser.safe_find_element(driver, By.ID, "expose-title")

        if offer_title != "Unknown":
            print("Found Offer title, scriping the rest.")
            offer_location = StealthBrowser.safe_find_element(driver, By.CLASS_NAME, "zip-region-and-country")
            agent_name = StealthBrowser.safe_find_element(driver, By.CLASS_NAME, "truncateChild_5TDve")
            real_estate_agency = StealthBrowser.safe_find_element(driver, By.CSS_SELECTOR, "p[data-qa='company-name']")
            kalt_price = StealthBrowser.safe_find_element(driver, By.CLASS_NAME, "is24-preis-value")
            flat_size = StealthBrowser.safe_find_element(driver, By.CLASS_NAME, "is24qa-wohnflaeche-main")
            number_of_rooms = StealthBrowser.safe_find_element(driver, By.CLASS_NAME, "is24qa-zi-main")
            nebekosten = StealthBrowser.safe_find_element(driver, By.CLASS_NAME, "is24qa-nebenkosten")
            total_price = StealthBrowser.safe_find_element(driver, By.CSS_SELECTOR, "dd.is24qa-gesamtmiete")
            construction_year = StealthBrowser.safe_find_element(driver, By.CLASS_NAME, "is24qa-baujahr")
            description = StealthBrowser.safe_find_element(driver, By.CLASS_NAME, "is24qa-objektbeschreibung")
            area_description = StealthBrowser.safe_find_element(driver, By.CLASS_NAME, "is24qa-lage")
            
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
            print(f"Expose {expose_id} scraped to database.")
            StealthBrowser.perform_random_action(driver)
            return True
        
    except Exception:
        print("Not valid offer title found, bad attempt!")
        return False


def apply_for_offer(driver, expose_id):
    print("Trying application...")
    try:
        message_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "Button_button-primary__6QTnx"))
        )
        message_button.click()
        print("Message button found and clicked successfully.")
    except Exception as e:
        print("Failed to find or click message button.", e)
        return False

    StealthBrowser.perform_random_action(driver)

    if "Welcome - ImmobilienScout24" in driver.title:
        print("User not logged in. Bad attempt")
        return False

    if "MieterPlus freischalten | ImmoScout24" in driver.title:
        print("MieterPlus page detected. Skipping expose.")
        database.mark_expose_as_processed(expose_id)
        print(f"Expose {expose_id} marked as processed.")
        return True

    try:
        StealthBrowser.random_wait(driver)
        message_label = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "label[for='message']"))
        )
        message_box = driver.find_element(By.ID, "message")
        message_box.clear()
    except:
        print("Message pop-up did not open or message box not found, bad attempt")
        return False

    message_box.send_keys(APPLICATION_TEXT)
    print("Application text entered successfully.")

    StealthBrowser.perform_random_action(driver)

    try:
        send_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button[type='submit'].Button_button-primary__6QTnx"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", send_button)
        send_button.click()
        print("Submit clicked, waiting for confirmation.")
    except:
        print("Submit not fount!")
        return False

    confirmation_message = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//h2[text()='Nachricht gesendet']"))
    )
    if confirmation_message:
        database.mark_expose_as_processed(expose_id)
        print(f"Expose {expose_id} marked as processed.")
        # TO-DO Notify user?
        return True
    else:
        # TO-DO Handle unfilled form fields
        print("Failed to send message or fill the form.", e)
        return False

def handle_page(driver, expose_id):
    page_title = driver.title
    print(f"Page title: {page_title}")
    

    if immo_page_titles['cookie_wall'] in page_title:
        print("Cookie wall detected, waiting for user input.")
        driver.wait_for_user()
    elif immo_page_titles['offer_expired'] in page_title or immo_page_titles['offer_deactivated'] in page_title:
        print("Offer expired or deactivated, skipping.")
        database.mark_expose_as_processed(expose_id)
        print(f"Expose {expose_id} marked as processed.")
        return False
    elif immo_page_titles['login_page'] in page_title:
        print("Login page detected, waiting for manual login.")
        perform_login(driver)
    elif immo_page_titles['error_page'] in page_title or immo_page_titles['home_page'] in page_title:
        print("Error or landed on home page, skipping.")
        return False

    StealthBrowser.perform_random_action(driver)
    # Could be a good offer, let´s check
    #Can we scrape it?
    if not scrape_expose(driver, expose_id):
        return False

    # Are we logged in?
    if not check_login(driver):
        return False
    
    # Can we apply?
    if not apply_for_offer(driver,expose_id):
        return False
    
    return True

def process_expose(driver, expose):
    expose_id = expose['expose_id']
    offer_link = generate_immobilienscout_link(expose)
    print(f"Processing expose from Immobilienscout24: {offer_link}")
    # Number of attempts
    max_attempts = 3
    # Loop through attempts
    for attempt in range(1, max_attempts + 1):
        print(f"Attempt {attempt}...")
        driver.get(offer_link)
        driver.load_cookies(driver, "immobilienscout24")
        StealthBrowser.random_wait(driver)
        WebDriverWait(driver, 120).until(lambda driver: driver.title != "")
        if handle_page(driver, expose_id):
            print("Attempt {attempt} succeeded!")
            return True
        else:
            print("Attempt {attempt} failed.")
            if attempt < max_attempts:
                print("Retrying...\n")
                StealthBrowser.random_wait(driver)
            else:
                print("All attempts failed for expose ID {expose_id}.")
                database.increase_failures_count(expose_id)
                return False


