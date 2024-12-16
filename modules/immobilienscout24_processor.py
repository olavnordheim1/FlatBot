
import os
import time
import base64
import re
from modules.Expose import Expose
from modules.BaseExposeProcessor import BaseExposeProcessor
from modules.StealthBrowser import StealthBrowser
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv




class Immobilienscout24_processor(BaseExposeProcessor):
    name = "Immobilienscout24"
    domain = "immobilienscout24.de"

    def __init__(self):
   
        # Load environment variables
        load_dotenv()
        IMMO_EMAIL = base64.b64decode(os.getenv("IMMO_EMAIL")).decode("utf-8")
        IMMO_PASSWORD = base64.b64decode(os.getenv("IMMO_PASSWORD")).decode("utf-8")
        APPLICATION_TEXT = os.getenv("DEFAULT_APPLICATION_TEXT")

        super().__init__(IMMO_EMAIL, IMMO_PASSWORD, APPLICATION_TEXT)

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

    #Returns updated Expose object
    def _handle_page(self, Expose, StealthBrowser):
        page_title = StealthBrowser.title
        self._debug_log(f"Page title: {page_title}")
        

        if self.immo_page_titles['cookie_wall'] in page_title:
            self._debug_log("Cookie wall detected, waiting for user input.")
            StealthBrowser.wait_for_user()
        elif self.immo_page_titles['offer_expired'] in page_title or self.immo_page_titles['offer_deactivated'] in page_title:
            self._debug_log("Offer expired or deactivated, skipping.")
            Expose.processed = True
            self._debug_log(f"Expose {Expose.expose_id} marked as processed.")
            return Expose, False
        elif self.immo_page_titles['login_page'] in page_title:
            self._debug_log("Login page detected, waiting for manual login.")
            self._perform_login(StealthBrowser)
        elif self.immo_page_titles['error_page'] in page_title or self.immo_page_titles['home_page'] in page_title:
            self._debug_log("Error or landed on home page, skipping.")
            return Expose, False

        StealthBrowser.perform_random_action()
        # Could be a good offer, let´s check
        #Can we scrape it?
        Expose, scraped = self._scrape_expose(Expose, StealthBrowser)
        if not scraped:
            return Expose, False

        # Are we logged in?
        if not self._check_login(StealthBrowser):
            return Expose, False
        
        # Can we apply?
        Expose, applied = self._apply_for_offer(StealthBrowser, Expose)
        if not applied:
            return Expose, False      
        return Expose, True

    ###############################
    ####### IMMO FUNCTIONS ########
    ###############################
    
    def _check_login(self, StealthBrowser):
        # Check login status based on page elements
        try:
            login_header = StealthBrowser.find_element(By.CLASS_NAME, "topnavigation__sso-login__header")
            if login_header and "angemeldet als" in login_header.text:
                self._debug_log("User already logged in.")
                return True
        except Exception:
            self._debug_log("User does not seems to be logged in")
            return False
        
    def _perform_login(self, StealthBrowser):
        try:
            login_link = StealthBrowser.find_element(By.CLASS_NAME, "topnavigation__sso-login__middle")
            if login_link and "Anmelden" in login_link.text:
                self._debug_log("User not logged in. Attempting login.")
                login_link.click()
                try:
                    StealthBrowser.random_wait()
                    email_field = WebDriverWait(StealthBrowser, 10).until(
                        EC.presence_of_element_located((By.ID, "username"))
                    )
                    email_field.send_keys(self.email)
                    self._debug_log("Email entered successfully.")
                    StealthBrowser.perform_random_action()

                    submit_button = WebDriverWait(StealthBrowser, 10).until(
                        EC.presence_of_element_located((By.ID, "submit"))
                    )
                    StealthBrowser.random_mouse_movements(submit_button)
                    submit_button.click()
                    self._debug_log("Email submission successful, waiting for password field.")

                    StealthBrowser.random_wait()
                    password_field = WebDriverWait(StealthBrowser, 10).until(
                        EC.presence_of_element_located((By.ID, "password"))
                    )
                    password_field.send_keys(self.password)
                    self._debug_log("Password entered successfully.")
                    StealthBrowser.perform_random_action()

                    remember_me_checkbox = WebDriverWait(StealthBrowser, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "label[for='rememberMeCheckBox']"))
                    )
                    StealthBrowser.random_mouse_movements(remember_me_checkbox)
                    #remember_me_checkbox.click()
                    #self._debug_log("'Remember Me' checkbox selected.")
                    StealthBrowser.perform_random_action()
                    login_button = WebDriverWait(StealthBrowser, 10).until(
                        EC.presence_of_element_located((By.ID, "loginOrRegistration"))
                    )
                    StealthBrowser.random_mouse_movements(login_button)
                    login_button.click()
                    self._debug_log("Login submitted successfully.")

                    ## TO-DO validate success

                    StealthBrowser.save_cookies(self.name)
                    StealthBrowser.refresh()
                    self._debug_log("Page reloaded after login.")
                    return True
                except Exception as e:
                    self._debug_log("Login failed.", e)
                    #browser_helpers.wait_for_user()
                    # TO-DO Notify user
                    return False                           
        except Exception:
            self._debug_log("Login button not found.", e)
            #browser_helpers.wait_for_user()
            # TO-DO Notify user
            return False
        

    def _scrape_expose(self, Expose, StealthBrowser):
        # Check title
        try:
            offer_title = StealthBrowser.safe_find_element(By.ID, "expose-title")

            if offer_title != "Unknown":
                self._debug_log("Found Offer title, scriping the rest.")
                Expose.location = StealthBrowser.safe_find_element(By.CLASS_NAME, "zip-region-and-country")
                Expose.agent_name = StealthBrowser.safe_find_element(By.CLASS_NAME, "truncateChild_5TDve")
                Expose.real_estate_agency = StealthBrowser.safe_find_element(By.CSS_SELECTOR, "p[data-qa='company-name']")
                Expose.price_kalt = StealthBrowser.safe_find_element(By.CLASS_NAME, "is24-preis-value")
                Expose.square_meters = StealthBrowser.safe_find_element(By.CLASS_NAME, "is24qa-wohnflaeche-main")
                Expose.number_of_rooms = StealthBrowser.safe_find_element(By.CLASS_NAME, "is24qa-zi-main")
                Expose.nebekosten = StealthBrowser.safe_find_element(By.CLASS_NAME, "is24qa-nebenkosten")
                Expose.price_warm = StealthBrowser.safe_find_element(By.CSS_SELECTOR, "dd.is24qa-gesamtmiete")
                Expose.construction_year = StealthBrowser.safe_find_element(By.CLASS_NAME, "is24qa-baujahr")
                Expose.description = StealthBrowser.safe_find_element(By.CLASS_NAME, "is24qa-objektbeschreibung")
                Expose.neighborhood = StealthBrowser.safe_find_element(By.CLASS_NAME, "is24qa-lage")
                
                self._debug_log(f"Expose {Expose.expose_id} scraped to database.")
                StealthBrowser.perform_random_action()
                return Expose, True
            
        except Exception:
            self._debug_log("Not valid offer title found, bad attempt!")
            return Expose, False
        

    def _apply_for_offer(self, StealthBrowser, Expose):
        self._debug_log("Trying application...")
        try:
            message_button = WebDriverWait(StealthBrowser, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "Button_button-primary__6QTnx"))
            )
            message_button.click()
            self._debug_log("Message button found and clicked successfully.")
        except Exception as e:
            self._debug_log("Failed to find or click message button.", e)
            return Expose, False

        StealthBrowser.perform_random_action()

        if "Welcome - ImmobilienScout24" in StealthBrowser.title:
            self._debug_log("User not logged in. Bad attempt")
            return Expose, False

        if "MieterPlus freischalten | ImmoScout24" in StealthBrowser.title:
            self._debug_log("MieterPlus page detected. Skipping expose.")
            # moved in process_expose
            #database.mark_expose_as_processed(expose_id)
            self._debug_log(f"Expose {Expose.expose_id} marked as processed.")
            Expose.processed = True
            return Expose, True

        try:
            StealthBrowser.random_wait()
            message_label = WebDriverWait(StealthBrowser, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "label[for='message']"))
            )
            message_box = StealthBrowser.find_element(By.ID, "message")
            message_box.clear()
        except:
            self._debug_log("Message pop-up did not open or message box not found, bad attempt")
            return Expose, False

        message_box.send_keys(self.application_text)
        self._debug_log("Application text entered successfully.")

        StealthBrowser.perform_random_action()

        try:
            send_button = WebDriverWait(StealthBrowser, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button[type='submit'].Button_button-primary__6QTnx"))
            )
            StealthBrowser.execute_script("arguments[0].scrollIntoView(true);", send_button)
            send_button.click()
            self._debug_log("Submit clicked, waiting for confirmation.")
        except:
            self._debug_log("Submit not fount!")
            return Expose, False

        confirmation_message = WebDriverWait(StealthBrowser, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[text()='Nachricht gesendet']"))
        )
        if confirmation_message:
            # moved in process_expose
            #database.mark_expose_as_processed(expose_id)
            self._debug_log(f"Expose {Expose.expose_id} applied succesfully.")
            # TO-DO Notify user?
            return Expose, True
        else:
            # TO-DO Handle unfilled form fields
            self._debug_log("Failed to send message or fill the form.", e)
            return Expose, False
