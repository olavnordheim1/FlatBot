
import os
import base64
import re
import logging
from modules.Expose import Expose
from modules.BaseExposeProcessor import BaseExposeProcessor
from modules.StealthBrowser import StealthBrowser
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class Immobilienscout24_processor(BaseExposeProcessor):
    name = "Immobilienscout24"
    domain = "immobilienscout24.de"

    def __init__(self):
   
        # Load environment variables
        load_dotenv()
        IMMO_EMAIL = base64.b64decode(os.getenv("IMMO_EMAIL")).decode("utf-8")
        IMMO_PASSWORD = base64.b64decode(os.getenv("IMMO_PASSWORD")).decode("utf-8")

        super().__init__(IMMO_EMAIL, IMMO_PASSWORD)

        self.immo_page_titles = {
            "cookie_wall": "Ich bin kein Roboter",
            "offer_expired": "Angebot nicht gefunden4",
            "offer_deactivated": "Angebot wurde deaktiviert",
            "login_page": "Welcome - ImmobilienScout24",
            "error_page": "Fehler",
            "home_page": "ImmoScout24 – Die Nr. 1 für Immobilien"
        }

    @staticmethod
    def extract_expose_link(subject, email_body):
        #Extract unique expose links from the email body specific to Immobilienscout24#

    	# Filter Keywords
        subject_keywords = {"angebot", "offer"}

        # Normalize keywords to lowercase for consistent matching
        subject_keywords = {keyword.lower() for keyword in subject_keywords}

        # Check subject filter before processing
        subject_lower = subject.lower()
        if not any(keyword in subject_lower for keyword in subject_keywords):
            return []

        # Extract expose links using a regex pattern
        pattern = re.compile(r"https:\/\/[a-zA-Z0-9./?=&_-]*expose/(\d+)")
        return list(set(pattern.findall(email_body)))
    
    @staticmethod
    def _generate_expose_link(Expose):
        offer_link = f"https://push.search.is24.de/email/expose/{Expose.expose_id}"
        return offer_link

    #Returns updated Expose object, called in process_expose
    def _handle_page(self, Expose):
        page_title = self.stealth_chrome.title
        logger.debug(f"Page title: {page_title}")
        

        if self.immo_page_titles['cookie_wall'] in page_title:
            logger.warning("Cookie wall detected, waiting for user input.")
            self.stealth_chrome.wait_for_user()
        elif self.immo_page_titles['offer_expired'] in page_title or self.immo_page_titles['offer_deactivated'] in page_title:
            logger.debug("Offer expired or deactivated, skipping.")
            Expose.processed = True
            logger.debug(f"Expose {Expose.expose_id} marked as processed.")
            return Expose, False
        elif self.immo_page_titles['login_page'] in page_title:
            logger.warning("Login page detected, attempting login.")
            self._perform_login()
        elif self.immo_page_titles['error_page'] in page_title or self.immo_page_titles['home_page'] in page_title:
            logger.warning("Error or landed on home page, skipping.")
            return Expose, False

        self.stealth_chrome.perform_random_action()
        # Could be a good offer, let´s check
        #Can we scrape it?
        Expose, scraped = self._scrape_expose(Expose)
        if not scraped:
            return Expose, False

        # Are we logged in?
        if not self._check_login():
            return Expose, False
        
        # Can we apply?
        Expose, applied = self._apply_for_offer(Expose)
        if not applied:
            return Expose, False      
        return Expose, True

    ###############################
    ####### IMMO FUNCTIONS ########
    ###############################
    
    def _check_login(self):
        # Check login status based on page elements
        try:
            login_header = self.stealth_chrome.find_element(By.CLASS_NAME, "topnavigation__sso-login__header")
            if login_header and "angemeldet als" in login_header.text:
                logger.debug("User already logged in.")
                return True
        except Exception:
            logger.debug("User does not seems to be logged in")
            return False
        
    def _perform_login(self):
        try:
            login_link = self.stealth_chrome.find_element(By.CLASS_NAME, "topnavigation__sso-login__middle")
            if login_link and "Anmelden" in login_link.text:
                logger.debug("User not logged in. Attempting login.")
                login_link.click()
                try:
                    self.stealth_chrome.random_wait()
                    email_field = WebDriverWait(self.stealth_chrome, 10).until(
                        EC.presence_of_element_located((By.ID, "username"))
                    )
                    email_field.send_keys(self.email)
                    logger.debug("Email entered successfully.")
                    self.stealth_chrome.perform_random_action()

                    submit_button = WebDriverWait(self.stealth_chrome, 10).until(
                        EC.presence_of_element_located((By.ID, "submit"))
                    )
                    self.stealth_chrome.random_mouse_movements(submit_button)
                    submit_button.click()
                    logger.debugg("Email submission successful, waiting for password field.")

                    self.stealth_chrome.random_wait()
                    password_field = WebDriverWait(self.stealth_chrome, 10).until(
                        EC.presence_of_element_located((By.ID, "password"))
                    )
                    password_field.send_keys(self.password)
                    logger.debug("Password entered successfully.")
                    self.stealth_chrome.perform_random_action()

                    remember_me_checkbox = WebDriverWait(self.stealth_chrome, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "label[for='rememberMeCheckBox']"))
                    )
                    self.stealth_chrome.random_mouse_movements(remember_me_checkbox)
                    #remember_me_checkbox.click()
                    #logger.debug("'Remember Me' checkbox selected.")
                    self.stealth_chrome.perform_random_action()
                    login_button = WebDriverWait(self.stealth_chrome, 10).until(
                        EC.presence_of_element_located((By.ID, "loginOrRegistration"))
                    )
                    self.stealth_chrome.random_mouse_movements(login_button)
                    login_button.click()
                    logger.nfo("Login submitted successfully.")

                    ## TO-DO validate success

                    self.stealth_chrome.save_cookies(self.name)
                    self.stealth_chrome.refresh()
                    logger.debug("Page reloaded after login.")
                    return True
                except Exception as e:
                    logger.warning("Login failed.", e)
                    #self.stealth_chrome_helpers.wait_for_user()
                    # TO-DO Notify user
                    return False                           
        except Exception:
            logger.debug("Login button not found.", e)
            #self.stealth_chrome_helpers.wait_for_user()
            # TO-DO Notify user
            return False
        

    def _scrape_expose(self, Expose):
        # Check title
        try:
            offer_title = self.stealth_chrome.safe_find_element(By.ID, "expose-title")

            if offer_title != "Unknown":
                logger.debug("Found Offer title, scriping the rest.")
                Expose.location = self.stealth_chrome.safe_find_element(By.CLASS_NAME, "zip-region-and-country")
                Expose.agent_name = self.stealth_chrome.safe_find_element(By.CLASS_NAME, "truncateChild_5TDve")
                Expose.real_estate_agency = self.stealth_chrome.safe_find_element(By.CSS_SELECTOR, "p[data-qa='company-name']")
                Expose.price_kalt = self.stealth_chrome.safe_find_element(By.CLASS_NAME, "is24-preis-value")
                Expose.square_meters = self.stealth_chrome.safe_find_element(By.CLASS_NAME, "is24qa-wohnflaeche-main")
                Expose.number_of_rooms = self.stealth_chrome.safe_find_element(By.CLASS_NAME, "is24qa-zi-main")
                Expose.nebekosten = self.stealth_chrome.safe_find_element(By.CLASS_NAME, "is24qa-nebenkosten")
                Expose.price_warm = self.stealth_chrome.safe_find_element(By.CSS_SELECTOR, "dd.is24qa-gesamtmiete")
                Expose.construction_year = self.stealth_chrome.safe_find_element(By.CLASS_NAME, "is24qa-baujahr")
                Expose.description = self.stealth_chrome.safe_find_element(By.CLASS_NAME, "is24qa-objektbeschreibung")
                Expose.neighborhood = self.stealth_chrome.safe_find_element(By.CLASS_NAME, "is24qa-lage")
                
                logger.info(f"Expose {Expose.expose_id} scraped to database.")
                self.stealth_chrome.perform_random_action()
                return Expose, True
            
        except Exception:
            logger.warning("Not valid offer title found, bad attempt!")
            return Expose, False
        

    def _apply_for_offer(self, Expose):
        logger.debug("Trying application...")
        try:
            message_button = WebDriverWait(self.stealth_chrome, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "Button_button-primary__6QTnx"))
            )
            message_button.click()
            logger.debug("Message button found and clicked successfully.")
        except Exception as e:
            logger.debug("Failed to find or click message button.", e)
            return Expose, False

        self.stealth_chrome.perform_random_action()

        if "Welcome - ImmobilienScout24" in self.stealth_chrome.title:
            logger.debug("User not logged in. Bad attempt")
            return Expose, False

        if "MieterPlus freischalten | ImmoScout24" in self.stealth_chrome.title:
            logger.info("MieterPlus page detected. Skipping expose.")
            # moved in process_expose
            #database.mark_expose_as_processed(expose_id)
            logger.debug(f"Expose {Expose.expose_id} marked as processed.")
            Expose.processed = True
            return Expose, True

        try:
            self.stealth_chrome.random_wait()
            message_label = WebDriverWait(self.stealth_chrome, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "label[for='message']"))
            )
            message_box = self.stealth_chrome.find_element(By.ID, "message")
            message_box.clear()
        except:
            logger.warning("Message pop-up did not open or message box not found, bad attempt")
            return Expose, False

        self._fill_application_form(Expose)
        logger.debug("Application text entered successfully.")

        self.stealth_chrome.perform_random_action()

        try:
            send_button = WebDriverWait(self.stealth_chrome, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button[type='submit'].Button_button-primary__6QTnx"))
            )
            self.stealth_chrome.execute_script("arguments[0].scrollIntoView(true);", send_button)
            send_button.click()
            logger.debug("Submit clicked, waiting for confirmation.")
        except:
            logger.debug("Submit not fount!")
            return Expose, False

        confirmation_message = WebDriverWait(self.stealth_chrome, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[text()='Nachricht gesendet']"))
        )
        if confirmation_message:
            # moved in process_expose
            #database.mark_expose_as_processed(expose_id)
            logger.info(f"Expose {Expose.expose_id} applied succesfully.")
            # TO-DO Notify user?
            return Expose, True
        else:
            # TO-DO Handle unfilled form fields
            logger.warning("Failed to send message or fill the form.", e)
            return Expose, False

    def _accept_cookies(self):
        """
        Clicks the 'Accept All' cookie button if present.
        """
        try:
            # Wait for the button to be clickable
            button = self.stealth_chrome.wait.until(
                lambda driver: driver.find_element(By.CSS_SELECTOR, "[data-testid='uc-accept-all-button']")
            )
            self.stealth_chrome.random_mouse_movements(button)
            button.click()
            logging.info("Successfully clicked the 'Accept All' button.")
        except Exception as e:
            logging.error(f"Failed to click the 'Accept All' button: {e}")

    def _fill_application_form(self, Expose):
    # Initialize filling values (customize these as needed)
        form_values = {
            "vonplz": "12045",
            "nachplz": "",
            "message": self.ApplicationGenerator.generate_application(Expose),
            "salutation": "MALE",
            "=firstName": "Marco",
            "lastName": "Chinello",
            "phoneNumber": "015734813927",
            "=street": "Sonnenallee",
            "houseNumber": "71",
            "postcode": "12045",
            "city": "Berlin",
            "moveInDateType": "Flexible",
            "numberOfPersons": "1",
            "has=": "FALSE",
            "=employmentRelationship": "WORKER",
            "income": "OVER_2000_UPTO_3000",
            "applicationPackageCompleted": "TRUE",
            "sendUserProfile": "TRUE",
            "hasPets": "FALSE",
            "sendUser=": "TRUE",
            "=sendUserProfile": "TRUE"
        }

        for field_name, value in form_values.items():
            try:
                # Attempt to locate the field using various attributes
                field = self.stealth_chrome.find_element(By.NAME, field_name)

                # Simulate human-like mouse movements
                self.stealth_chrome.random_mouse_movements(field)

                # Handle different field types
                tag_name = field.tag_name.lower()
                field_type = field.get_attribute("type").lower() if field.get_attribute("type") else ""

                if tag_name == "input" and field_type in ["text", "email", "tel", "number"]:
                    field.clear()
                    field.send_keys(value)
                    self.stealth_chrome.random_wait()
                elif tag_name == "textarea":
                    field.clear()
                    field.send_keys(value)
                    self.stealth_chrome.random_wait()
                elif tag_name == "select":
                    Select(field).select_by_visible_text(value)
                    self.stealth_chrome.random_wait()
                elif tag_name == "input" and field_type == "checkbox":
                    current_state = field.is_selected()
                    if value.lower() in ["true", "yes", "1"] and not current_state:
                        field.click()
                    elif value.lower() in ["false", "no", "0"] and current_state:
                        field.click()
                    self.stealth_chrome.random_wait()
            except Exception as e:
                logging.debug(f"Could not fill field '{field_name}': {e}")

        logging.info("Form filling completed.")
